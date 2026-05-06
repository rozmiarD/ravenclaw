from __future__ import annotations

import re
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List

from action_compiler import compile_action_spec  # type: ignore
from campaign_utils import extract_host_from_url, host_in_scope, load_scope_domains  # type: ignore
from policy_core import get_approved_spec_allowed_tools, get_runtime_allowed_tools, contains_tool_restricted_patterns, normalize_tool  # type: ignore
from sclite.integrity import artifact_descriptor  # type: ignore
from tool_registry import get_tool_catalog  # type: ignore

HOST_TOKEN_RE = re.compile(r"(https?://[^\s\"'<>]+)|\b((?:[a-z0-9-]+\.)+[a-z]{2,})\b", re.IGNORECASE)


class ExecutionEngine:
    def __init__(self) -> None:
        self.scope_domains = load_scope_domains()
        self.artifacts_root = Path.cwd() / 'tmp' / 'engine-handoffs'
        self.tool_catalog = get_tool_catalog()

    def _normalize_argv(self, tool: str, args: List[Any], *, approved_spec: bool = False) -> List[str]:
        norm_tool = normalize_tool(tool)
        if not norm_tool:
            raise ValueError('missing_tool')
        allowed_tools = get_approved_spec_allowed_tools() if approved_spec else get_runtime_allowed_tools()
        if norm_tool not in allowed_tools:
            reason = 'tool_not_allowed_for_approved_spec' if approved_spec else 'tool_not_allowed'
            raise ValueError(f'{reason}:{norm_tool}')
        normalized_args = [str(a) for a in (args or [])]
        if norm_tool == 'curl' and '-q' not in normalized_args and '--disable' not in normalized_args:
            normalized_args = ['-q'] + normalized_args
        restricted, restricted_pattern = contains_tool_restricted_patterns(norm_tool, normalized_args)
        if restricted:
            raise ValueError(f'tool_restricted_pattern:{norm_tool}:{restricted_pattern}')
        return [norm_tool] + normalized_args

    def _extract_hosts_from_text(self, text: Any) -> List[str]:
        raw = str(text or '').strip()
        if not raw:
            return []
        raw_lower = raw.lower()
        if raw_lower.startswith('file://'):
            return []
        hosts: List[str] = []
        seen: set[str] = set()
        direct = str(extract_host_from_url(raw) or '').strip().lower()
        if direct:
            seen.add(direct)
            hosts.append(direct)
        allow_bare_domain_match = ('/' not in raw and '\\' not in raw) or 'host:' in raw_lower
        for match in HOST_TOKEN_RE.finditer(raw):
            if match.group(1):
                token = str(match.group(1) or '').strip().lower()
            else:
                if not allow_bare_domain_match:
                    continue
                token = str(match.group(2) or '').strip().lower()
            host = str(extract_host_from_url(token) or token).strip().lower()
            if host and host not in seen:
                seen.add(host)
                hosts.append(host)
        return hosts

    def _arg_target_observations(self, argv: List[str], stdin_text: Any = '') -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {'urls': [], 'hosts': [], 'files': []}
        seen: Dict[str, set[str]] = {'urls': set(), 'hosts': set(), 'files': set()}

        def _observe(raw_value: Any) -> None:
            raw = str(raw_value or '').strip()
            if not raw or raw.startswith('-'):
                return
            lowered = raw.lower()
            if lowered.startswith(('http://', 'https://')):
                if lowered not in seen['urls']:
                    seen['urls'].add(lowered)
                    out['urls'].append(raw)
                return
            if lowered.startswith('file://'):
                if lowered not in seen['files']:
                    seen['files'].add(lowered)
                    out['files'].append(raw)
                return
            if any(ch.isspace() for ch in raw) or '/' in raw or '\\' in raw:
                return
            host = str(extract_host_from_url(raw) or raw).strip().lower()
            if not host or '.' not in host:
                return
            if host not in seen['hosts']:
                seen['hosts'].add(host)
                out['hosts'].append(host)

        for token in argv[1:]:
            _observe(token)
        for line in str(stdin_text or '').splitlines():
            _observe(line)
        return out

    def _enforce_target_semantics(self, argv: List[str], stdin_text: Any = '') -> None:
        tool = normalize_tool(argv[0] if argv else '')
        if not tool:
            return
        info = self.tool_catalog.get(tool) or {}
        target_validation_mode = str(info.get('target_validation_mode') or 'none').strip().lower() or 'none'
        observed = self._arg_target_observations(argv, stdin_text=stdin_text)

        if target_validation_mode == 'strict_url':
            if observed['files'] and not observed['urls']:
                return
            if not observed['urls']:
                raise ValueError(f'missing_target_kind:{tool}:url')
            return

        if target_validation_mode == 'strict_host_domain':
            if observed['urls']:
                raise ValueError(f'invalid_target_kind:{tool}:url')
            if not observed['hosts']:
                raise ValueError(f'missing_target_kind:{tool}:host_or_domain')

    def _enforce_scope(self, argv: List[str], stdin_text: Any = '') -> None:
        self._enforce_target_semantics(argv, stdin_text=stdin_text)
        for token in [*argv[1:], *str(stdin_text or '').splitlines()]:
            for host in self._extract_hosts_from_text(token):
                if not host_in_scope(host, self.scope_domains):
                    raise ValueError(f'out_of_scope_target:{host}')

    def _artifact_run_dir(self) -> Path:
        run_dir = self.artifacts_root / str(uuid.uuid4())
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _write_step_artifacts(self, run_dir: Path, step_index: int, stdout: str, stderr: str) -> Dict[str, str]:
        stdout_path = run_dir / f'step_{step_index}_stdout.txt'
        stderr_path = run_dir / f'step_{step_index}_stderr.txt'
        stdout_path.write_text(stdout or '', encoding='utf-8')
        stderr_path.write_text(stderr or '', encoding='utf-8')
        return {
            'stdout_path': str(stdout_path),
            'stderr_path': str(stderr_path),
            'stdout_first_line': str((stdout or '').splitlines()[0] if (stdout or '').splitlines() else ''),
            'stderr_first_line': str((stderr or '').splitlines()[0] if (stderr or '').splitlines() else ''),
        }

    def _expand_step_args(self, args: List[Any], artifacts: List[Dict[str, str]]) -> List[str]:
        out: List[str] = []
        previous = artifacts[-1] if artifacts else {}
        for raw in (args or []):
            token = str(raw)
            if token == '{prev_stdout_path}':
                out.append(str(previous.get('stdout_path') or ''))
                continue
            if token == '{prev_stderr_path}':
                out.append(str(previous.get('stderr_path') or ''))
                continue
            if token == '{prev_stdout_first_line}':
                out.append(str(previous.get('stdout_first_line') or ''))
                continue
            if token == '{prev_stderr_first_line}':
                out.append(str(previous.get('stderr_first_line') or ''))
                continue
            out.append(token)
        return out

    def build_execution_plan(self, action_spec: Dict[str, Any]) -> List[List[str]]:
        compiled = compile_action_spec(action_spec)
        plan = compiled.get('execution_plan') if isinstance(compiled.get('execution_plan'), list) else []
        if plan:
            out: List[List[str]] = []
            for step in plan:
                if not isinstance(step, dict):
                    continue
                out.append(self._normalize_argv(str(step.get('tool') or ''), list(step.get('args') or [])))
            if out:
                return out
        return [self._normalize_argv(str(compiled.get('tool') or ''), list(compiled.get('args') or []))]

    def build_command(self, action_spec: Dict[str, Any]) -> List[str]:
        plan = self.build_execution_plan(action_spec)
        return plan[0]

    def _validate_approved_execution_spec(self, approved_execution_spec: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(approved_execution_spec, dict):
            raise ValueError('invalid_approved_execution_spec')
        spec_version = str(approved_execution_spec.get('spec_version') or '').strip()
        if spec_version != '2026-03-18.approved.v1':
            raise ValueError(f'invalid_approved_execution_spec_version:{spec_version or "missing"}')
        approval = approved_execution_spec.get('approval') if isinstance(approved_execution_spec.get('approval'), dict) else {}
        decision = str(approval.get('decision') or '').strip().lower()
        if decision != 'approve':
            raise ValueError(f'invalid_approved_execution_decision:{decision or "missing"}')
        execution_truth = approved_execution_spec.get('execution_truth') if isinstance(approved_execution_spec.get('execution_truth'), dict) else {}
        artifact_type = str(execution_truth.get('artifact_type') or '').strip()
        if artifact_type != 'approved_execution_spec':
            raise ValueError(f'invalid_approved_execution_truth_artifact:{artifact_type or "missing"}')
        return execution_truth

    def _approved_execution_steps(self, approved_execution_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        execution_truth = self._validate_approved_execution_spec(approved_execution_spec)
        execution_plan = execution_truth.get('execution_plan') if isinstance(execution_truth, dict) else approved_execution_spec.get('execution_plan')
        if not isinstance(execution_plan, list) or not execution_plan:
            raise ValueError('missing_execution_plan')
        out: List[Dict[str, Any]] = []
        for step in execution_plan:
            if not isinstance(step, dict):
                continue
            normalized_step = {'tool': str(step.get('tool') or ''), 'args': list(step.get('args') or [])}
            if step.get('stdin'):
                normalized_step['stdin'] = str(step.get('stdin') or '')
            out.append(normalized_step)
        if not out:
            raise ValueError('missing_execution_plan')
        return out

    def build_execution_plan_from_approved_spec(self, approved_execution_spec: Dict[str, Any]) -> List[List[str]]:
        out: List[List[str]] = []
        for step in self._approved_execution_steps(approved_execution_spec):
            out.append(self._normalize_argv(str(step.get('tool') or ''), list(step.get('args') or []), approved_spec=True))
        if not out:
            raise ValueError('missing_execution_plan')
        return out

    def _validate_execution_ticket_gate(
        self,
        approved_execution_spec: Dict[str, Any],
        *,
        execution_ticket: Dict[str, Any] | None,
        execution_contract: Dict[str, Any] | None,
        raw_steps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not isinstance(execution_ticket, dict):
            raise ValueError('missing_execution_ticket')
        if not isinstance(execution_contract, dict):
            raise ValueError('missing_execution_contract')
        artifact_type = str(execution_ticket.get('artifact_type') or '').strip()
        schema_version = str(execution_ticket.get('schema_version') or '').strip()
        if artifact_type != 'execution_ticket' or schema_version != 'v0.2':
            raise ValueError(f'invalid_execution_ticket:{artifact_type or "missing"}:{schema_version or "missing"}')
        approval = execution_ticket.get('approval') if isinstance(execution_ticket.get('approval'), dict) else {}
        status = str(approval.get('status') or '').strip().lower()
        if status != 'approve':
            raise ValueError(f'invalid_execution_ticket_approval:{status or "missing"}')
        limits = execution_ticket.get('execution_limits') if isinstance(execution_ticket.get('execution_limits'), dict) else {}
        try:
            max_runs = int(limits.get('max_runs', 0) or 0)
        except (TypeError, ValueError):
            max_runs = 0
        if max_runs < 1:
            raise ValueError('invalid_execution_ticket_max_runs')
        contract_digest = artifact_descriptor(execution_contract)['digest']
        integrity = execution_ticket.get('integrity') if isinstance(execution_ticket.get('integrity'), dict) else {}
        bound_digest = str(integrity.get('ticket_binds_execution_contract_digest') or '').strip()
        if bound_digest != contract_digest:
            raise ValueError('execution_ticket_contract_digest_mismatch')
        shape = execution_contract.get('execution_shape') if isinstance(execution_contract.get('execution_shape'), dict) else {}
        contract_plan = shape.get('plan') if isinstance(shape.get('plan'), list) else []
        if len(contract_plan) != len(raw_steps):
            raise ValueError('execution_ticket_plan_length_mismatch')
        for idx, (contract_step, approved_step) in enumerate(zip(contract_plan, raw_steps), 1):
            if not isinstance(contract_step, dict):
                raise ValueError(f'execution_ticket_invalid_contract_step:{idx}')
            if str(contract_step.get('tool') or '') != str(approved_step.get('tool') or ''):
                raise ValueError(f'execution_ticket_tool_mismatch:{idx}')
            if [str(item) for item in list(contract_step.get('args') or [])] != [str(item) for item in list(approved_step.get('args') or [])]:
                raise ValueError(f'execution_ticket_args_mismatch:{idx}')
        return {
            'status': 'passed',
            'ticket_id': str(execution_ticket.get('ticket_id') or ''),
            'execution_contract_digest': contract_digest,
            'profile': str(integrity.get('profile') or ''),
        }

    def execute_approved_spec(
        self,
        approved_execution_spec: Dict[str, Any],
        dry_run: bool = False,
        *,
        execution_ticket: Dict[str, Any] | None = None,
        execution_contract: Dict[str, Any] | None = None,
        require_execution_ticket: bool = False,
    ) -> Dict[str, Any]:
        raw_steps = self._approved_execution_steps(approved_execution_spec)
        execution_ticket_gate = None
        if require_execution_ticket:
            execution_ticket_gate = self._validate_execution_ticket_gate(
                approved_execution_spec,
                execution_ticket=execution_ticket,
                execution_contract=execution_contract,
                raw_steps=raw_steps,
            )
        plan = [self._normalize_argv(str(step.get('tool') or ''), list(step.get('args') or []), approved_spec=True) for step in raw_steps]
        compiled = {
            'action_type': str(approved_execution_spec.get('action_type') or ''),
            'capability': str(approved_execution_spec.get('capability') or ''),
            'compiler_tool_choice': str(approved_execution_spec.get('resolved_tool') or ''),
            'compiler_tool_choice_source': 'approved_execution_spec',
            'execution_mode': str(approved_execution_spec.get('execution_mode') or ''),
            'semantic_loss_policy': dict((approved_execution_spec.get('compiler') or {}).get('semantic_loss_policy') or {}) if isinstance(approved_execution_spec.get('compiler'), dict) else {},
        }
        if dry_run:
            for step, argv in zip(raw_steps, plan):
                self._enforce_scope(argv, stdin_text=step.get('stdin') or '')
            return {
                'status': 'dry-run',
                'returncode': 0,
                'stdout': '',
                'stderr': '',
                'reason': 'dry_run_requested',
                'compiled_action': compiled,
                'planned_commands': plan,
                'execution_source': 'approved_execution_spec',
                'execution_ticket_gate': execution_ticket_gate or {'status': 'not_required'},
            }

        combined_stdout: List[str] = []
        combined_stderr: List[str] = []
        executed_commands: List[List[str]] = []
        step_artifacts: List[Dict[str, str]] = []
        run_dir = self._artifact_run_dir()
        last_rc = 0
        for idx, step in enumerate(raw_steps, 1):
            argv = self._normalize_argv(str(step.get('tool') or ''), self._expand_step_args(list(step.get('args') or []), step_artifacts), approved_spec=True)
            stdin_text = str(step.get('stdin') or '')
            self._enforce_scope(argv, stdin_text=stdin_text)
            executed_commands.append(argv)
            proc = subprocess.run(argv, input=stdin_text or None, capture_output=True, text=True)
            last_rc = int(proc.returncode)
            artifacts = self._write_step_artifacts(run_dir, idx, proc.stdout or '', proc.stderr or '')
            step_artifacts.append(artifacts)
            step_header = f'=== step_{idx}:{argv[0]} ==='
            if proc.stdout:
                combined_stdout.append(step_header + '\n' + proc.stdout)
            if proc.stderr:
                combined_stderr.append(step_header + '\n' + proc.stderr)
            if proc.returncode != 0:
                return {
                    'status': 'failed',
                    'returncode': proc.returncode,
                    'stdout': '\n\n'.join(combined_stdout),
                    'stderr': '\n\n'.join(combined_stderr),
                    'reason': f'command_failed:{argv[0]}',
                    'compiled_action': compiled,
                    'planned_commands': plan,
                    'executed_commands': executed_commands,
                    'step_artifacts': step_artifacts,
                    'execution_source': 'approved_execution_spec',
                    'execution_ticket_gate': execution_ticket_gate or {'status': 'not_required'},
                }
        return {
            'status': 'succeeded',
            'returncode': last_rc,
            'stdout': '\n\n'.join(combined_stdout),
            'stderr': '\n\n'.join(combined_stderr),
            'reason': 'ok',
            'compiled_action': compiled,
            'planned_commands': plan,
            'executed_commands': executed_commands,
            'step_artifacts': step_artifacts,
            'execution_source': 'approved_execution_spec',
            'execution_ticket_gate': execution_ticket_gate or {'status': 'not_required'},
        }

    def execute(self, action_spec: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        compiled = compile_action_spec(action_spec)
        plan = self.build_execution_plan(action_spec)
        raw_plan = compiled.get('execution_plan') if isinstance(compiled.get('execution_plan'), list) else []
        if dry_run:
            for step, argv in zip(raw_plan, plan):
                if not isinstance(step, dict):
                    continue
                self._enforce_scope(argv, stdin_text=step.get('stdin') or '')
            return {
                'status': 'dry-run',
                'returncode': 0,
                'stdout': '',
                'stderr': '',
                'reason': 'dry_run_requested',
                'compiled_action': compiled,
                'planned_commands': plan,
                'execution_source': 'legacy_direct_action_spec',
            }

        combined_stdout: List[str] = []
        combined_stderr: List[str] = []
        executed_commands: List[List[str]] = []
        step_artifacts: List[Dict[str, str]] = []
        run_dir = self._artifact_run_dir()
        last_rc = 0
        for idx, step in enumerate(raw_plan, 1):
            if not isinstance(step, dict):
                continue
            argv = self._normalize_argv(str(step.get('tool') or ''), self._expand_step_args(list(step.get('args') or []), step_artifacts))
            stdin_text = str(step.get('stdin') or '')
            self._enforce_scope(argv, stdin_text=stdin_text)
            executed_commands.append(argv)
            proc = subprocess.run(argv, input=stdin_text or None, capture_output=True, text=True)
            last_rc = int(proc.returncode)
            artifacts = self._write_step_artifacts(run_dir, idx, proc.stdout or '', proc.stderr or '')
            step_artifacts.append(artifacts)
            step_header = f'=== step_{idx}:{argv[0]} ==='
            if proc.stdout:
                combined_stdout.append(step_header + '\n' + proc.stdout)
            if proc.stderr:
                combined_stderr.append(step_header + '\n' + proc.stderr)
            if proc.returncode != 0:
                return {
                    'status': 'failed',
                    'returncode': proc.returncode,
                    'stdout': '\n\n'.join(combined_stdout),
                    'stderr': '\n\n'.join(combined_stderr),
                    'reason': f'command_failed:{argv[0]}',
                    'compiled_action': compiled,
                    'planned_commands': plan,
                    'executed_commands': executed_commands,
                    'step_artifacts': step_artifacts,
                    'execution_source': 'legacy_direct_action_spec',
                }

        return {
            'status': 'succeeded',
            'returncode': last_rc,
            'stdout': '\n\n'.join(combined_stdout),
            'stderr': '\n\n'.join(combined_stderr),
            'reason': 'ok',
            'compiled_action': compiled,
            'planned_commands': plan,
            'executed_commands': executed_commands,
            'step_artifacts': step_artifacts,
            'execution_source': 'legacy_direct_action_spec',
        }


ExecutorEngine = ExecutionEngine


if __name__ == '__main__':
    engine = ExecutionEngine()
    print(engine.build_command({'tool': 'curl', 'args': ['https://example.com'], 'capability': 'http_probe'}))
