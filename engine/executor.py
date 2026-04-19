from __future__ import annotations

import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List

from action_compiler import compile_action_spec  # type: ignore
from campaign_utils import extract_host_from_url, host_in_scope, load_scope_domains  # type: ignore
from execution_contracts import build_command_preview_from_execution_spec  # type: ignore
from policy_core import get_approved_spec_allowed_tools, get_runtime_allowed_tools, normalize_tool  # type: ignore


class ExecutionEngine:
    def __init__(self) -> None:
        self.scope_domains = load_scope_domains()
        self.artifacts_root = Path.cwd() / 'tmp' / 'engine-handoffs'

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
        return [norm_tool] + normalized_args

    def _enforce_scope(self, argv: List[str]) -> None:
        for token in argv[1:]:
            host = extract_host_from_url(str(token))
            if host and not host_in_scope(host, self.scope_domains):
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

    def _approved_execution_steps(self, approved_execution_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not isinstance(approved_execution_spec, dict):
            raise ValueError('invalid_approved_execution_spec')
        execution_truth = approved_execution_spec.get('execution_truth') if isinstance(approved_execution_spec.get('execution_truth'), dict) else {}
        execution_plan = execution_truth.get('execution_plan') if isinstance(execution_truth, dict) else approved_execution_spec.get('execution_plan')
        if isinstance(execution_plan, list) and execution_plan:
            out: List[Dict[str, Any]] = []
            for step in execution_plan:
                if not isinstance(step, dict):
                    continue
                out.append({'tool': str(step.get('tool') or ''), 'args': list(step.get('args') or [])})
            if out:
                return out
        preview = build_command_preview_from_execution_spec(approved_execution_spec)
        if not preview:
            raise ValueError('missing_execution_plan')
        return [{'tool': str(preview[0] or ''), 'args': list(preview[1:])}]

    def build_execution_plan_from_approved_spec(self, approved_execution_spec: Dict[str, Any]) -> List[List[str]]:
        out: List[List[str]] = []
        for step in self._approved_execution_steps(approved_execution_spec):
            out.append(self._normalize_argv(str(step.get('tool') or ''), list(step.get('args') or []), approved_spec=True))
        if not out:
            raise ValueError('missing_execution_plan')
        return out

    def execute_approved_spec(self, approved_execution_spec: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        raw_steps = self._approved_execution_steps(approved_execution_spec)
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
            for argv in plan:
                self._enforce_scope(argv)
            return {
                'status': 'dry-run',
                'returncode': 0,
                'stdout': '',
                'stderr': '',
                'reason': 'dry_run_requested',
                'compiled_action': compiled,
                'planned_commands': plan,
                'execution_source': 'approved_execution_spec',
            }

        combined_stdout: List[str] = []
        combined_stderr: List[str] = []
        executed_commands: List[List[str]] = []
        step_artifacts: List[Dict[str, str]] = []
        run_dir = self._artifact_run_dir()
        last_rc = 0
        for idx, step in enumerate(raw_steps, 1):
            argv = self._normalize_argv(str(step.get('tool') or ''), self._expand_step_args(list(step.get('args') or []), step_artifacts), approved_spec=True)
            self._enforce_scope(argv)
            executed_commands.append(argv)
            proc = subprocess.run(argv, capture_output=True, text=True)
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
        }

    def execute(self, action_spec: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        compiled = compile_action_spec(action_spec)
        plan = self.build_execution_plan(action_spec)
        if dry_run:
            for argv in plan:
                self._enforce_scope(argv)
            return {
                'status': 'dry-run',
                'returncode': 0,
                'stdout': '',
                'stderr': '',
                'reason': 'dry_run_requested',
                'compiled_action': compiled,
                'planned_commands': plan,
            }

        combined_stdout: List[str] = []
        combined_stderr: List[str] = []
        executed_commands: List[List[str]] = []
        step_artifacts: List[Dict[str, str]] = []
        run_dir = self._artifact_run_dir()
        last_rc = 0
        raw_plan = compiled.get('execution_plan') if isinstance(compiled.get('execution_plan'), list) else []
        for idx, step in enumerate(raw_plan, 1):
            if not isinstance(step, dict):
                continue
            argv = self._normalize_argv(str(step.get('tool') or ''), self._expand_step_args(list(step.get('args') or []), step_artifacts))
            self._enforce_scope(argv)
            executed_commands.append(argv)
            proc = subprocess.run(argv, capture_output=True, text=True)
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
        }


ExecutorEngine = ExecutionEngine


if __name__ == '__main__':
    engine = ExecutionEngine()
    print(engine.build_command({'tool': 'curl', 'args': ['https://example.com'], 'capability': 'http_probe'}))
