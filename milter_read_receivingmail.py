import smtplib
import traceback
from datetime import datetime
from email.mime.text import MIMEText
import Milter
import psycopg2
from cryptography.fernet import Fernet# Mesaj gövdesini biriktir

#deneme
class EmailMilter(Milter.Base):
    def __init__(self):
        self.id = Milter.uniqueID()
        self.sender = None
        self.recipients = []
        self.message_data = b""

    def envfrom(self, mailfrom, *args):
        self.sender = mailfrom
        print(f"Gönderen: {mailfrom}")
        return Milter.CONTINUE

    def envrcpt(self, to, *args):
        self.recipients.append(to)
        print(f"Alıcı: {to}")
        return Milter.CONTINUE

    def eom(self):
        try:
            conn = psycopg2.connect(dbname="dbname", user="dbuser", password="dbpassword", host="dbhost", port="dbport")
            cursor = conn.cursor()
            FERNET_KEY_PASS_CUST = 'your secret key'
            for recipient in self.recipients:

                clean_recipient = recipient.strip('<>')
                cursor.execute("SELECT contents FROM dbtable WHERE contents->>'username' = %s", (clean_recipient,))
                alias_data = cursor.fetchone()
                print("1", alias_data)
                cursor.execute("select * from dbtable WHERE contents->>'username' = %s", (clean_recipient,))
                username_data = cursor.fetchone()
                if not username_data:
                    continue

                user_data = username_data[1]
                if 'password' not in user_data:
                    continue
                plain_password = Fernet(FERNET_KEY_PASS_CUST).decrypt(str(user_data['password']).encode()).decode()
                print(plain_password)

                if alias_data:

                    alias = alias_data[0]
                    first_date = datetime.strptime(alias['first_date'], "%d.%m.%Y")
                    last_date = datetime.strptime(alias['last_date'], "%d.%m.%Y")
                    subject = alias['subject']
                    body = alias['body']
                    current_time = datetime.now()

                    if first_date <= current_time <= last_date:
                        auto_reply_subject = f"Otomatik Yanıt: {subject}"
                        auto_reply_body = body
                        auto_reply = MIMEText(auto_reply_body)
                        auto_reply["Subject"] = auto_reply_subject
                        auto_reply["From"] = clean_recipient
                        auto_reply["To"] = self.sender

                        with smtplib.SMTP("mail.domain.com", 587) as server:

                            server.starttls()
                            server.login(clean_recipient, plain_password)
                            server.sendmail(recipient, self.sender, auto_reply.as_string())

            cursor.close()
            conn.close()

        except Exception as e:
            traceback.print_exc()

        return Milter.CONTINUE

    def body(self, chunk):
        self.message_data += chunk
        return Milter.CONTINUE

    def close(self):

        return Milter.CONTINUE


if __name__ == "__main__":
    Milter.factory = EmailMilter
    print("inet:48186@127.0.0.1")
    Milter.runmilter("PythonMilter", "inet:48186@127.0.0.1")
