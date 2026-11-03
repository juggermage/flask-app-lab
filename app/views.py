from flask import render_template, request, flash, redirect, url_for

from . import app
from .forms import ContactForm
from .logging_utils import log_contact

PROFILE = {
    "name": "Руслан Залєвський",
    "role": "Junior Python / Flask розробник",
    "about": (
        "Студент 3 курсу, цікавлюсь веброзробкою та backend-технологіями. "
        "Пишу чистий код, швидко вчуся та працюю в команді. "
        "Шукаю можливість отримати перший практичний досвід у розробці."
    ),
}

EDUCATION = [
    {
        "years": "2024 – теперішній час",
        "place": "Карпатський національний університет імені Василя Стефаника",
        "degree": "Бакалавр, Інженерія програмного забезпечення",
    },
    {
        "years": "2013 – 2024",
        "place": "Ліцей №13, м. Івано-Франківськ",
        "degree": "Повна загальна середня освіта",
    },
]

SKILLS = [
    "Командна робота",
    "Самонавчання",
    "Аналітичне мислення",
    "Англійська мова (B1)",
    "Вирішення проблем",
]

TECHNOLOGIES = [
    "Python", "Flask", "HTML", "CSS",
    "Bootstrap", "Git / GitHub", "SQL",
]

PROJECTS = [
    {
        "title": "Flask-сайт «Резюме»",
        "period": "2026",
        "description": "Навчальний вебзастосунок із маршрутизацією, шаблонами Jinja2 та Bootstrap.",
        "stack": ["Python", "Flask", "Bootstrap"],
    },
    {
        "title": "Телеграм-бот для нагадувань",
        "period": "2025",
        "description": "Бот, що зберігає нагадування користувача та надсилає їх у потрібний час.",
        "stack": ["Python", "SQLite"],
    },
    {
        "title": "Персональний лендінг",
        "period": "2025",
        "description": "Адаптивна одностор­інкова сторінка з власним дизайном.",
        "stack": ["HTML", "CSS", "JavaScript"],
    },
]

CONTACTS = {
    "email": "ruslan.zalievskyi.24@pnu.edu.ua",
    "phone": "+380 50 312 32 54",
    "city": "Івано-Франківськ, Україна",
    "github": "https://github.com/juggermage",
}



@app.context_processor
def inject_profile():
    """Робить profile доступним у всіх шаблонах (base, navbar, footer),
    зокрема й у шаблонах блюпринтів."""
    return {"profile": PROFILE}


@app.route("/")
def main():
    return render_template("index.html", title="Головна")


@app.route("/homepage")
def home():
    """View for the Home page of your website."""
    agent = request.user_agent
    return render_template("homepage.html", title="Homepage", agent=agent)


@app.route("/resume")
def resume():
    return render_template(
        "resume.html",
        title="Резюме",  # динамічний заголовок сторінки
        education=EDUCATION,
        skills=SKILLS,
        technologies=TECHNOLOGIES,
        projects=PROJECTS,
    )


@app.route("/contacts", methods=["GET", "POST"])
def contacts():
    form = ContactForm()

    if form.validate_on_submit():
        subject_label = dict(form.subject.choices).get(form.subject.data, form.subject.data)
        record = {
            "name": form.name.data,
            "email": form.email.data,
            "phone": form.phone.data or "",
            "subject": subject_label,
            "message": form.message.data,
        }
        try:
            log_contact(app.config["CONTACT_LOG_PATH"], record)
        except OSError:
            flash("Не вдалося записати ваші дані. Спробуйте пізніше.", "danger")
        else:
            flash(f"Дякуємо, {record['name']}! Повідомлення надіслано, дані збережено.", "success")
        return redirect(url_for("contacts"))  # Post/Redirect/Get

    if request.method == "POST":
        flash("Форму не надіслано: перевірте виділені поля.", "danger")

    return render_template("contacts.html", title="Контакти", contacts=CONTACTS, form=form)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", title="Не знайдено"), 404
