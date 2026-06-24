import aiohttp
from urllib.parse import urlencode
import docx2txt
import asyncio
import os
import aspose.words as aw
from datetime import datetime
from aiogram.types import FSInputFile
from db import Database
import logging


class SendScheduleImage:
    def __init__(self):
        self.page_mapping = {
            "5а": "image1.png",
            "5б": "image1.png",
            "5в": "image1.png",
            "5г": "image1.png",
            "5д": "image1.png",
            "5е": "image1.png",
            "5ж": "image1.png",
            "5з": "image1.png",
            "6а": "image1.png",
            "6б": "image1.png",
            "6в": "image2.png",
            "6г": "image2.png",
            "6д": "image2.png",
            "6е": "image2.png",
            "6ж": "image2.png",
            "6и": "image2.png",
            "7а": "image2.png",
            "7б": "image2.png",
            "7в": "image2.png",
            "7г": "image2.png",
            "7д": "image3.png",
            "7ж": "image3.png",
            "7з": "image3.png",
            "8а": "image3.png",
            "8б": "image3.png",
            "8в": "image3.png",
            "8г": "image3.png",
            "8д": "image3.png",
            "8е": "image3.png",
            "9а": "image3.png",
            "9б": "image4.png",
            "9в": "image4.png",
            "9г": "image4.png",
            "9д": "image4.png",
            "9е": "image4.png",
            "10а": "image4.png",
            "10б": "image4.png",
            "11а": "image4.png",
        }
        self.file_name = "schedule"
        self.folder_path = "temp"
        self.file_path = f"{self.folder_path}/{self.file_name}.docx"
        os.makedirs(self.folder_path, exist_ok=True)

    async def get_page_mapping(self):
        return self.page_mapping

    async def download_file(self, output_file):
        """Асинхронно скачивает файл расписания с Яндекс.Диска."""
        base_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?"
        public_key = "https://disk.yandex.ru/i/eeUOub_4jL2IqA"

        final_url = base_url + urlencode(dict(public_key=public_key))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(final_url) as response:
                    if response.status != 200:
                        raise Exception(
                            f"Ошибка при получении ссылки на скачивание: {response.status}"
                        )
                    data = await response.json()
                    download_url = data["href"]

                async with session.get(download_url) as download_response:
                    if download_response.status != 200:
                        raise Exception(
                            f"Ошибка при скачивании файла: {download_response.status}"
                        )

                    file_path = os.path.join(self.folder_path, f"{output_file}.docx")
                    file_content = await download_response.read()

                    # Записываем файл в отдельном потоке, чтобы не блокировать event loop
                    await asyncio.to_thread(self._write_file, file_path, file_content)

            return file_path
        except Exception as e:
            logging.error(f"Ошибка при скачивании файла: {e}")
            raise

    def _write_file(self, file_path: str, content: bytes):
        """Синхронная функция для записи файла (вызывается в отдельном потоке)."""
        with open(file_path, "wb") as f:
            f.write(content)

    def get_images_from_docx(self):
        """Извлекает изображения из DOCX файла."""
        try:
            docx2txt.process(self.file_path, self.folder_path)
        except Exception as e:
            logging.error(f"Ошибка при извлечении изображений из DOCX: {e}")
            raise

    def compare_docx(self, file1, file2):
        """Сравнивает два DOCX файла. Возвращает True, если файлы отличаются."""
        try:
            doc1 = aw.Document(file1)
            doc2 = aw.Document(file2)
            doc1.compare(doc2, "user", datetime.today())
            return doc1.revisions.count > 0
        except Exception as e:
            logging.error(f"Ошибка при сравнении файлов: {e}")
            # В случае ошибки считаем, что файлы отличаются, чтобы не пропустить обновление
            return True

    async def check_new_schedule(self, bot, db):
        """Проверяет наличие нового расписания каждые 10 минут."""
        import logging

        # Инициализация: извлекаем изображения из существующего файла
        if os.path.exists(self.file_path):
            try:
                self.get_images_from_docx()
            except Exception as e:
                logging.error(
                    f"Ошибка при извлечении изображений при инициализации: {e}"
                )

        while True:
            try:
                logging.info("Проверка нового расписания...")

                if not os.path.exists(self.file_path):
                    logging.warning("Файл расписания не найден")
                    await asyncio.sleep(600)
                    continue

                # Скачиваем новую версию файла
                try:
                    temp_file = await self.download_file(self.file_name + "_temp")
                except Exception as e:
                    logging.error(f"Ошибка при загрузке нового файла: {e}")
                    await asyncio.sleep(600)
                    continue

                if not os.path.exists(temp_file):
                    logging.warning("Не удалось загрузить новый файл")
                    await asyncio.sleep(600)
                    continue

                # Сравниваем файлы
                try:
                    files_differ = self.compare_docx(self.file_path, temp_file)
                except Exception as e:
                    logging.error(f"Ошибка при сравнении файлов: {e}")
                    os.remove(temp_file)
                    await asyncio.sleep(600)
                    continue

                if files_differ:
                    logging.info("Обнаружено новое расписание")

                    # Удаляем старый файл
                    try:
                        os.remove(self.file_path)
                    except Exception as e:
                        logging.warning(f"Не удалось удалить старый файл: {e}")

                    # Переименовываем новый файл
                    try:
                        os.rename(temp_file, self.file_path)
                    except Exception as e:
                        logging.error(f"Не удалось переименовать файл: {e}")
                        await asyncio.sleep(600)
                        continue

                    # Удаляем старые изображения
                    try:
                        for file_name in os.listdir(self.folder_path):
                            if "image" in file_name and file_name.endswith(".png"):
                                file_path = os.path.join(self.folder_path, file_name)
                                if os.path.isfile(file_path):
                                    os.remove(file_path)
                    except Exception as e:
                        logging.warning(f"Ошибка при удалении старых изображений: {e}")

                    # Извлекаем новые изображения
                    try:
                        self.get_images_from_docx()
                    except Exception as e:
                        logging.error(f"Ошибка при извлечении изображений: {e}")
                        await asyncio.sleep(600)
                        continue

                    # Отправляем расписание всем пользователям
                    await self.send_schedule_images_for_all(bot, db)
                    logging.info("Расписание успешно обновлено и отправлено")
                else:
                    logging.info("Расписание не изменилось")
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        logging.warning(f"Не удалось удалить временный файл: {e}")

            except Exception as e:
                logging.error(f"Критическая ошибка в цикле проверки расписания: {e}")

            await asyncio.sleep(600)

    def get_image_name(self, grade):
        return f"{self.folder_path}/{self.page_mapping.get(grade)}"

    async def send_schedule_images_for_all(self, bot, db):
        """Отправляет новое расписание всем активным пользователям."""
        users = db.get_active_users()
        success_count = 0
        error_count = 0

        for user in users:
            try:
                grade_key = f"{user[1]}{user[2].lower()}"
                image_path = self.get_image_name(grade_key)

                if not os.path.exists(image_path):
                    logging.warning(
                        f"Изображение не найдено для пользователя {user[0]}: {image_path}"
                    )
                    error_count += 1
                    continue

                await bot.send_photo(
                    chat_id=user[0],
                    photo=FSInputFile(image_path),
                    caption="Доступно новое расписание!",
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                logging.warning(
                    f"Не удалось отправить расписание пользователю {user[0]}: {e}"
                )

        logging.info(
            f"Расписание отправлено {success_count} пользователям, ошибок: {error_count}"
        )

    async def send_schedule_images_for_one(self, message, db, user_id):
        """Отправляет расписание одному пользователю."""
        user = db.get_user_for_schedule(user_id)
        if not user:
            await message.answer(
                "Пользователь не найден или неактивен. Пожалуйста, используйте /settings для настройки."
            )
            return

        try:
            grade_key = f"{user[1]}{user[2].lower()}"
            image_path = self.get_image_name(grade_key)

            if not os.path.exists(image_path):
                await message.answer(
                    "Извините, расписание для вашего класса временно недоступно."
                )
                return

            await message.answer_photo(photo=FSInputFile(image_path))
        except Exception as e:
            logging.error(f"Ошибка при отправке расписания пользователю {user_id}: {e}")
            await message.answer(
                "Произошла ошибка при отправке расписания. Попробуйте позже."
            )
