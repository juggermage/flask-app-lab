from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "lab2-dev-secret-key"

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


@app.route("/")
@app.route("/resume")
def resume():
    return render_template(
        "resume.html",
        title="Резюме",  # динамічний заголовок сторінки
        profile=PROFILE,
        education=EDUCATION,
        skills=SKILLS,
        technologies=TECHNOLOGIES,
        projects=PROJECTS,
    )


@app.route("/contacts", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        # Форма-заглушка: дані нікуди не відправляються
        name = request.form.get("name", "").strip()
        flash(f"Дякуємо, {name}! Повідомлення отримано (демо-режим, без відправки).", "success")
        return redirect(url_for("contacts"))
    return render_template("contacts.html", title="Контакти", contacts=CONTACTS, profile=PROFILE)


if __name__ == "__main__":
    app.run(debug=True)
