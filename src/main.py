import asyncio
import os
from utils.logger import LoggerSingleton
from services.readers.mail_reader import procesar_correo_conexion_persistente

logger = LoggerSingleton.get_logger("main")

JOB_INTERVAL_SECONDS = 60
_job_lock = asyncio.Lock()

async def job():
    if _job_lock.locked():
        logger.warning("Job: ejecución anterior aún en curso; salto esta vez")
        return
    async with _job_lock:
        logger.info("Starting scheduled job (async)...")
        try:            
            procesar_correo_conexion_persistente(                                    
                                    os.getenv("MAIL_USER", "tecnicovirtual@apnprevent.es"),
                                    os.getenv("MAIL_PASS", "123456"),
                                    os.getenv("MAIL_SERVER", "172.26.0.114"),
                                    int(os.getenv("MAIL_PORT", "143")),
                                    "INBOX",  # o la carpeta que uses
            )
        except Exception as e:
            logger.exception("Error in scheduled job: %s", e)

async def scheduler():
    # Dispara una vez al inicio
    await job()
    # Bucle periódico sin aioschedule
    while True:
        # Lanza una ejecución (protegida por el lock)
        asyncio.create_task(job())
        await asyncio.sleep(JOB_INTERVAL_SECONDS)

if __name__ == "__main__":
    logger.info("Running async scheduled job...")
    asyncio.run(scheduler())
