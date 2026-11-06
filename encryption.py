import hashlib
import secrets
import base64
import hmac


class Encryption:
    @staticmethod
    def hash_pass(password) -> tuple[
        bytes, bytes]:  # хэшируем мастер пароль, соль - рандомная последовательность байтов
        """
        Регистрация
        :param password:
        :return: возвращает соль полученный хэш от мастерпароля переработанный через pbkdf2 и sha-256
        """
        salt = secrets.token_bytes(16)
        pass_hash = hashlib.pbkdf2_hmac('sha-256', password.encode(), salt, 600000)
        return pass_hash, salt

    @staticmethod
    def verify_pass(password, salt, exp_hash) -> bool:  # при попытке входа сверяем хэши
        """
        Авторизация
        :param password:
        :param salt:
        :param exp_hash:
        :return: True или False взависимости правильный ли пароль
        """
        pass_hash = hashlib.pbkdf2_hmac('sha-256', password.encode(), salt, 600000)
        return hmac.compare_digest(pass_hash, exp_hash)

    @staticmethod
    def derive_key(password, salt) -> bytes:
        """
        Принимаем мастер пароль, соль
        Применяем pbkdf2 и sha-256
        :param password:
        :param salt:
        :return: 32 битный ключ (позволяющий смотреть пароли)
        """
        key = hashlib.pbkdf2_hmac('sha-256', password.encode(), salt, 600000, dklen=32)
        return key

    @staticmethod
    def encrypt():


    @staticmethod
    def decrypt():
        pass
