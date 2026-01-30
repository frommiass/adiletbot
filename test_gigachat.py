from gigachat import GigaChat
import config


try:
    with GigaChat(
        credentials=config.GIGACHAT_CLIENT_SECRET,
        scope=config.GIGACHAT_SCOPE,
        verify_ssl_certs=False
    ) as giga:
        response = giga.chat("Привет! Ответь одним словом.")
        print("✅ GigaChat работает!")
        print(response.choices[0].message.content)
except Exception as e:
    print("❌ Ошибка:", e)




