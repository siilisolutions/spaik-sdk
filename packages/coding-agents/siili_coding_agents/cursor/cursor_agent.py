import asyncio
import uuid
from asyncio.subprocess import PIPE, create_subprocess_exec
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional

from siili_ai_sdk import MessageBlock, MessageBlockType

from .output_parser import parse_json_output, parse_stream_line


@dataclass
class CursorOptions:
    """Configuration options for Cursor CLI agent"""
    api_key: Optional[str] = None
    model: Optional[str] = None
    output_format: str = "json"
    working_directory: Optional[str] = None
    force: bool = False
    print_mode: bool = True  # Enable print mode by default for SDK use
    background: bool = False


class CursorAgent:
    """Wrapper for Cursor CLI that integrates with the Siili AI SDK"""
    
    def __init__(self, options: CursorOptions = CursorOptions(), yolo: bool = False):
        self.options = options
        self._session_id: Optional[str] = None
        if yolo:
            self.options.force = True
    
    def run(self, prompt: str) -> None:
        """Run Cursor CLI with the given prompt in blocking mode"""
        async def _run():
            async for message in self.stream_blocks(prompt):
                print(message.content if hasattr(message, 'content') else message)
        
        asyncio.run(_run())
    
    async def stream_blocks(self, prompt: str) -> AsyncGenerator[MessageBlock, None]:
        """Stream response blocks from Cursor CLI"""
        # Create session if none exists
        if not self._session_id:
            session_id = await self._create_new_session()
            if not session_id:
                yield MessageBlock(
                    id=str(uuid.uuid4()),
                    streaming=False,
                    type=MessageBlockType.ERROR,
                    content="Failed to create new chat session"
                )
                return
        
        cmd = self._build_command(prompt)
        
        try:
            process = await create_subprocess_exec(
                *cmd,
                stdout=PIPE,
                stderr=PIPE,
                cwd=self.options.working_directory
            )
            
            # Stream stdout
            collected_output: list[str] = []
            fmt = (self.options.output_format or "json").lower()
            if process.stdout:
                async for line in self._read_stream(process.stdout):
                    if not line.strip():
                        continue
                    if fmt == "stream-json":
                        for block in parse_stream_line(line):
                            yield block
                    elif fmt == "json":
                        collected_output.append(line)
                    else:
                        # text mode passthrough
                        yield MessageBlock(
                            id=str(uuid.uuid4()),
                            streaming=True,
                            type=MessageBlockType.PLAIN,
                            content=line
                        )
            
            # Wait for process completion
            return_code = await process.wait()
            
            # If json format, parse accumulated output now
            if fmt == "json" and collected_output:
                raw = "".join(collected_output)
                for block in parse_json_output(raw):
                    yield block

            # Handle stderr if there are errors
            if return_code != 0 and process.stderr:
                error_data = await process.stderr.read()
                error_text = error_data.decode('utf-8', errors='replace')
                if error_text.strip():
                    yield MessageBlock(
                        id=str(uuid.uuid4()),
                        streaming=False,
                        type=MessageBlockType.ERROR,
                        content=f"Cursor CLI error: {error_text}"
                    )
                        
        except FileNotFoundError:
            yield MessageBlock(
                id=str(uuid.uuid4()),
                streaming=False,
                type=MessageBlockType.ERROR,
                content="Cursor CLI not found. Please install it first: curl https://cursor.com/install -fsS | bash"
            )
        except Exception as e:
            yield MessageBlock(
                id=str(uuid.uuid4()),
                streaming=False,
                type=MessageBlockType.ERROR,
                content=f"Error executing Cursor CLI: {str(e)}"
            )
    
    async def resume_session(self, session_id: Optional[str] = None) -> AsyncGenerator[MessageBlock, None]:
        """Resume a previous Cursor CLI session"""
        cmd = ["cursor-agent"]
        
        if self.options.api_key:
            cmd.extend(["--api-key", self.options.api_key])
        
        # Ensure non-interactive mode to avoid hanging
        cmd.append("--print")
        fmt = self.options.output_format or "text"
        if fmt in ("text", "json", "stream-json"):
            cmd.extend(["--output-format", fmt])
        if self.options.force:
            cmd.append("--force")

        if session_id:
            cmd.extend(["--resume", session_id])
        else:
            cmd.append("resume")
        
        try:
            process = await create_subprocess_exec(
                *cmd,
                stdout=PIPE,
                stderr=PIPE,
                cwd=self.options.working_directory
            )
            
            if process.stdout:
                async for line in self._read_stream(process.stdout):
                    if line.strip():
                        yield MessageBlock(
                            id=str(uuid.uuid4()),
                            streaming=True,
                            type=MessageBlockType.PLAIN,
                            content=line
                        )
            
            await process.wait()
            
        except Exception as e:
            yield MessageBlock(
                id=str(uuid.uuid4()),
                streaming=False,
                type=MessageBlockType.ERROR,
                content=f"Error resuming Cursor session: {str(e)}"
            )
    
    async def list_sessions(self) -> list[Dict[str, Any]]:
        """List previous Cursor CLI sessions"""
        cmd = ["cursor-agent", "ls"]
        
        if self.options.api_key:
            cmd.extend(["--api-key", self.options.api_key])
        
        # Prefer non-interactive output for scripting
        cmd.append("--print")
        fmt = self.options.output_format or "text"
        if fmt in ("text", "json", "stream-json"):
            cmd.extend(["--output-format", fmt])
        if self.options.force:
            cmd.append("--force")
        
        try:
            process = await create_subprocess_exec(
                *cmd,
                stdout=PIPE,
                stderr=PIPE,
                cwd=self.options.working_directory
            )
            
            stdout_data, stderr_data = await process.communicate()
            
            if process.returncode == 0:
                output = stdout_data.decode('utf-8', errors='replace')
                # Parse the output - this depends on Cursor CLI's actual output format
                # For now, return raw output split by lines
                sessions = []
                for line in output.strip().split('\n'):
                    if line.strip():
                        sessions.append({"raw": line.strip()})
                return sessions
            else:
                error_text = stderr_data.decode('utf-8', errors='replace')
                raise Exception(f"Failed to list sessions: {error_text}")
                
        except Exception as e:
            raise Exception(f"Error listing Cursor sessions: {str(e)}")
    
    
    async def _create_new_session(self) -> Optional[str]:
        """Create a new chat session and return its ID"""
        cmd = ["cursor-agent", "create-chat"]
        
        if self.options.api_key:
            cmd.extend(["--api-key", self.options.api_key])
        
        # Ensure non-interactive mode
        cmd.append("--print")
        cmd.extend(["--output-format", "text"])
        
        try:
            process = await create_subprocess_exec(
                *cmd,
                stdout=PIPE,
                stderr=PIPE,
                cwd=self.options.working_directory
            )
            
            stdout_data, stderr_data = await process.communicate()
            
            if process.returncode == 0:
                session_id = stdout_data.decode('utf-8', errors='replace').strip()
                if session_id:
                    self._session_id = session_id
                    return session_id
            else:
                error_text = stderr_data.decode('utf-8', errors='replace')
                print(f"Failed to create session: {error_text}")
                
        except Exception as e:
            print(f"Error creating new session: {str(e)}")
            
        return None
    
    def clear_session(self) -> None:
        """Clear the current session ID from memory"""
        self._session_id = None
    
    def _build_command(self, prompt: str) -> list[str]:
        """Build the cursor-agent command with all options"""
        cmd = ["cursor-agent"]
        
        # Add API key if provided
        if self.options.api_key:
            cmd.extend(["--api-key", self.options.api_key])
        
        # Add model if specified
        if self.options.model:
            cmd.extend(["--model", self.options.model])
        
        # Add print mode if enabled
        if self.options.print_mode:
            cmd.append("--print")
            
        # Set output format
        fmt = self.options.output_format or "text"
        if fmt in ("text", "json", "stream-json"):
            cmd.extend(["--output-format", fmt])
            
        # Add force flag if enabled
        if self.options.force:
            cmd.append("--force")
            
        # Add background mode if enabled
        if self.options.background:
            cmd.append("--background")
        
        # Handle session resumption or creation
        if self._session_id:
            cmd.extend(["--resume", self._session_id])
        
        # Add the prompt
        cmd.append(prompt)
        
        return cmd
    
    async def _read_stream(self, stream):
        """Read lines from an async stream"""
        while True:
            try:
                line = await stream.readline()
                if not line:
                    break
                yield line.decode('utf-8', errors='replace')
            except Exception:
                break
