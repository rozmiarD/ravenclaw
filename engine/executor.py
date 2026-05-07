from __future__ import annotations

import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List

from action_compiler import compile_action_spec  # type: ignore
from campaign_utils import extract_host_from_url, host_in_scope, load_scope_domains  # type: ignore
from policy_core import get_approved_spec_allowed_tools, get_runtime_allowed_tools, contains_tool_restricted_patterns, normalize_tool  # type: ignore
from govengine.execution.approved_spec import approved_execution_steps, validate_approved_execution_spec
from govengine.execution.ticket_gate import validate_execution_ticket_gate
from govengine.execution.command_shape import (
    arg_target_observations,
    enforce_scope,
    enforce_target_semantics,
    extract_hosts_from_text,
    normalize_argv,
)
from govengine.scope import FunctionalScopePort
from tool_registry import get_tool_catalog  # type: ignore


class ExecutionEngine:
    def __init__(self) -> None:
        self.scope_domains = load_scope_domains()
        self.artifacts_root = Path.cwd() / 'tmp' / 'engine-handoffs'
        self.tool_catalog = get_tool_catalog()
        self.scope_port = FunctionalScopePort(extract_host_from_url, host_in_scope)

    def _normalize_argv(self, tool: str, args: List[Any], *, approved_spec: bool = False) -> List[str]:
        return normalize_argv(
            tool,
            args,
            allowed_tools=get_approved_spec_allowed_tools() if approved_spec else get_runtime_allowed_tools(),
            contains_tool_restricted_patterns=contains_tool_restricted_patterns,
            normalize_tool=normalize_tool,
            approved_spec=approved_spec,
        )

    def _extract_hosts_from_text(self, text: Any) -> List[str]:
        return extract_hosts_from_text(text, scope_port=self.scope_port)

    def _arg_target_observations(self, argv: List[str], stdin_text: Any = '') -> Dict[str, List[str]]:
        return arg_target_observations(argv, scope_port=self.scope_port, stdin_text=stdin_text)

    def _enforce_target_semantics(self, argv: List[str], stdin_text: Any = '') -> None:
        enforce_target_semantics(
            argv,
            tool_catalog=self.tool_catalog,
            normalize_tool=normalize_tool,
            scope_port=self.scope_port,
            stdin_text=stdin_text,
        )

    def _enforce_scope(self, argv: List[str], stdin_text: Any = '') -> None:
        enforce_scope(
            argv,
            scope_domains=self.scope_domains,
            host_in_scope=host_in_scope,
            tool_catalog=self.tool_catalog,
            normalize_tool=normalize_tool,
            scope_port=self.scope_port,
            stdin_text=stdin_text,
        )

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
        return validate_approved_execution_spec(approved_execution_spec)

    def _approved_execution_steps(self, approved_execution_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        return approved_execution_steps(approved_execution_spec)

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
        return validate_execution_ticket_gate(
            approved_execution_spec,
            execution_ticket=execution_ticket,
            execution_contract=execution_contract,
            raw_steps=raw_steps,
        )

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
