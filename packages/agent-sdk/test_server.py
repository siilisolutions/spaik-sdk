#!/usr/bin/env python3

import asyncio
import json
import sys

import aiohttp  # type: ignore

BASE_URL = "http://localhost:8000"


async def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Health check passed: {data}")
                return True
            else:
                print(f"❌ Health check failed with status {response.status}")
                return False


async def launch_job(message: str) -> str:
    """Launch a new job and return job_id"""
    print(f"🚀 Launching job with message: '{message}'")

    async with aiohttp.ClientSession() as session:
        payload = {"message": message}
        async with session.post(f"{BASE_URL}/jobs/launch", json=payload) as response:
            if response.status == 200:
                data = await response.json()
                job_id = data["job_id"]
                print(f"✅ Job launched successfully: {job_id}")
                return job_id
            else:
                error_text = await response.text()
                print(f"❌ Failed to launch job: {response.status} - {error_text}")
                raise Exception(f"Job launch failed: {response.status}")


async def stream_job_progress(job_id: str, session_id: str = "test_session"):
    """Stream job progress via SSE"""
    print(f"📡 Starting SSE stream for job {job_id}...")

    url = f"{BASE_URL}/jobs/{job_id}/stream?session_id={session_id}"
    print("🔄 Streaming events...")

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            print(f"🔄 Streaming events... {response.status}")
            if response.status != 200:
                error_text = await response.text()
                print(f"❌ Failed to start SSE stream: {response.status} - {error_text}")
                return

            print(f"📡 Connected! Headers: {dict(response.headers)}")
            event_count = 0
            buffer = ""

            # Read chunks and process SSE format
            async for chunk in response.content.iter_chunked(1024):
                if not chunk:
                    break

                chunk_str = chunk.decode("utf-8")
                buffer += chunk_str

                # Process complete lines
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line:
                        continue

                    print(f"📨 Raw line: {repr(line)}")

                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                        print(f"📨 Event: {event_type}")

                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            print(f"📦 Data: {json.dumps(data, indent=2)}")
                            event_count += 1

                            # Stop after receiving several events for demo
                            # if event_count >= 5:
                            #     print("🛑 Stopping stream after 5 events...")
                            #     return

                        except json.JSONDecodeError:
                            print(f"📦 Raw data: {data_str}")

                # Add small delay to make output readable
                await asyncio.sleep(0.1)

            print(f"✅ Stream completed, received {event_count} events")


async def test_multiple_sessions():
    """Test multiple sessions streaming the same job"""
    print("\n🔄 Testing multiple sessions...")

    # Launch a job
    job_id = await launch_job("Multi-session test message")

    # Create multiple streaming tasks
    tasks = []
    for i in range(3):
        session_id = f"session_{i}"
        task = asyncio.create_task(stream_job_progress(job_id, session_id))
        tasks.append(task)

    # Wait for all streams (with timeout)
    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=30.0)
    except asyncio.TimeoutError:
        print("⏰ Streams timed out after 30 seconds")


async def main():
    """Main test function"""
    print("🧪 Agent SDK Server Test Script")
    print("=" * 40)

    try:
        # Test health check first
        if not await test_health_check():
            print("❌ Server not healthy, exiting...")
            return

        print("\n" + "=" * 40)

        # Test single job launch and stream
        print("🔬 Test 1: Single job launch and stream")

        # Launch job and start streaming concurrently
        job_id = await launch_job("Hello, this is a test message!")

        # Start streaming task concurrently (don't wait for job to finish)
        stream_task = stream_job_progress(job_id)

        # Wait for streaming to complete
        await stream_task

        # print("\n" + "=" * 40)

        # # Test multiple sessions
        # print("🔬 Test 2: Multiple sessions")
        # await test_multiple_sessions()

        # print("\n" + "=" * 40)
        print("✅ All tests completed!")

    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Make sure the server is running with:")
    print("python siili_ai_sdk/server/playground/server.py")
    print("\nStarting tests in 3 seconds...")

    try:
        asyncio.sleep(3)  # type: ignore
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
