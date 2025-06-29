import asyncio
import logging
from typing import Callable, List, Any

# Cấu hình logging cơ bản
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Worker_pool_improved:
#num_workers: số worker chạy song song
#max_queue_size: giới hạn chiều dài hàng đợi
#back-pressure (raise khi queue đầy)
#metrics: tasks_completed, tasks_failed
#graceful shutdown
    def __init__(
        self,
            num_workers: int = 20,
            max_queue_size: int = 2000,
            submit_timeout: float = 2.0):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.num_workers = num_workers
        self.submit_timeout = submit_timeout
        self._workers: List[asyncio.Task] = []
        self._shutdown = False
        self.tasks_completed = 0
        self.tasks_failed = 0

    async def _worker(self, wid: int):
        logger.info(f"Worker-{wid} started")
        while not self._shutdown:
            try:
                func, args, kwargs = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue  # kiểm tra lại flag shutdown
            try:
                await func(*args, **kwargs)
                self.tasks_completed += 1
            except Exception as exc:
                self.tasks_failed += 1
                logger.exception(f"[Worker-{wid}] Task error")
            finally:
                self.queue.task_done()
        logger.info(f"Worker-{wid} stopped")

    async def start(self):
        for i in range(self.num_workers):
            w = asyncio.create_task(self._worker(i))
            self._workers.append(w)
        logger.info(f"Started {self.num_workers} workers")

    async def submit(self, func: Callable, *args: Any, **kwargs: Any):
        if self._shutdown:
            raise RuntimeError("Worker Pool đã dừng họat động")
        try:
            await asyncio.wait_for(
                self.queue.put((func, args, kwargs)),
                timeout=self.submit_timeout
            )
        except asyncio.TimeoutError:
            raise RuntimeError("WorkerPool đã đầy")

    async def stop(self):
        logger.info("WorkerPool shutdown initiated")
        self._shutdown = True
        # Đợi cho queue empty (nếu muốn đảm bảo xử lý hết task)
        await self.queue.join()
        # Cancel worker loops
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info(f"WorkerPool stopped: completed={self.tasks_completed}, failed={self.tasks_failed}")

