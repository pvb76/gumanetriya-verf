# Login and payment choices (Russia, checked 25.11.2026)

Facts from reference sites: small creators (webinars, consulting, one-off services) have no login at all; buyer leaves a contact or pays, product arrives by email or messenger. Accounts exist only for courses and subscription services (GetCourse: email+password, VK, Yandex; Skillbox: email, VK, Google, Yandex, Apple; Yandex Practicum: Yandex ID with phone, VK, OK, Mail, passkey, QR).

Default: guest checkout + "Мой заказ" by order number. Add login only for repeat access (courses, subscriptions, downloads).

| Method | Who can connect | Cost / effort | Use |
|---|---|---|---|
| Email code (magic link) | anyone | 0 ₽, own SMTP | first choice for an account |
| Yandex ID | any Yandex account owner, app at oauth.yandex.ru | 0 ₽, 10 min | yes |
| VK ID | app at id.vk.com/business/go | 0 ₽, 10 min | yes |
| MAX | verified legal entity / IP / self-employed on business.max.ru + bot moderation | 0 ₽, days | after verification |
| Phone SMS | SMS provider contract | paid per SMS | ask the user |
| Sber ID | organization or IP, offer via EDO, certificate | 0 ₽, weeks | not for self-employed |
| T-ID | from 30 000 logins per month | — | no |
| Google, Apple, Telegram Login | forbidden for Russian users on Russian sites | — | no |

Payment: YooKassa (cards, SBP) through the owner's automation; foreign cards via Lava.top. Self-employed: receipts through "Мой налог" integration of the provider. Never enable recurring charges without explicit consent text.
