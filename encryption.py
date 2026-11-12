import hashlib
import secrets
import hmac
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class Encryption:
    @staticmethod
    def hash_pass(password: str) -> tuple[
        bytes, bytes]:  # хэшируем мастер пароль, соль - рандомная последовательность байтов
        """
        Регистрация
        :param password:
        :return: возвращает соль полученный хэш от мастерпароля переработанный через pbkdf2 и sha-256
        """
        salt = secrets.token_bytes(16)
        pass_hash = hashlib.pbkdf2_hmac('sha-256', password.encode("utf-8"), salt, 600000)
        return pass_hash, salt

    @staticmethod
    def verify_pass(password: str, salt: bytes, exp_hash: bytes) -> bool:  # при попытке входа сверяем хэши
        """
        Авторизация
        :param password:
        :param salt:
        :param exp_hash:
        :return: True или False взависимости правильный ли пароль
        """
        pass_hash = hashlib.pbkdf2_hmac('sha-256', password.encode("utf-8"), salt, 600000)
        return hmac.compare_digest(pass_hash, exp_hash)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Принимаем мастер пароль, соль
        Применяем pbkdf2 и sha-256
        :param password:
        :param salt:
        :return: 32-байтовый (256-битный) ключ (позволяющий смотреть пароли)
        """
        key = hashlib.pbkdf2_hmac('sha-256', password.encode("utf-8"), salt, 600000, dklen=32)
        return key

    @staticmethod
    def encrypt(text: str, key: bytes) -> tuple[bytes, bytes]:
        """
        Шифрование
        Преобразуем пароль в байты
        Шифруем с помощью AESGCM и случайного nonce (пришлось прибегнуть сторонним библиотекам, иначе ну никак не зашифровать)
        :param text:
        :param key:
        :return: шифротекст и nonce
        """
        text_bytes = text.encode("utf-8")
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)
        encrypted_data = aesgcm.encrypt(nonce, text_bytes, None)
        return encrypted_data, nonce

    @staticmethod
    def decrypt(encrypted_data: bytes, nonce: bytes, key: bytes) -> str:
        aes = AESGCM(key)
        decrypted_data = aes.decrypt(nonce, encrypted_data, None)

        return decrypted_data.decode("utf-8")
