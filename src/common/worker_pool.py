import asyncio
from typing import Callable, List, Any


class WorkerPool:
    def __init__(self, num_workers: int, max_queue_size: int = 100):
        self.num_workers = num_workers
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.workers: List[asyncio.Task] = []

    async def worker(self):
        while True:
            task_func, args, kwargs = await self.queue.get()
            try:
                await task_func(*args, **kwargs)
            except Exception as e:
                print(f"Error in worker task: {e}")
            finally:
                self.queue.task_done()

    async def start(self):
        self.workers = [
            asyncio.create_task(self.worker())
            for _ in range(self.num_workers)
        ]

    async def stop(self):
        # Cancel all worker tasks
        for worker in self.workers:
            worker.cancel()

        # Wait for all worker tasks to be cancelled
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []

    async def submit(self, task_func: Callable, *args, **kwargs):
        await self.queue.put((task_func, args, kwargs))
