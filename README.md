# whatsapp_sound_bot

You always wanted to send audio messages to your friends and you don't have voice with you? grab this hack and implement as it yours own.

send text message to bot, which will return audio message.

# How to install
```
git clone https://github.com/whatsapp_sound_bot
cd whatsapp_sound_bot
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

git your number and run
```yowsup-cli registration -C <CountryCode> -r sms -p <Phone Number with Country Code>```
Then whatsapp will send a key via sms to the phone.
get that key then run:

```yowsup-cli registration -C 55 -R <sms-key> -p 554899998888```

In run.py
```CREDENT = ("number", "password") # replace with your phone and password```

```python run.py```
