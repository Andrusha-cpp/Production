// Находим форму
const form = document.getElementById("registerForm");

form.addEventListener("submit", function (event) {
    event.preventDefault(); // ❗ запрещаем обычную HTML-отправку

    // Собираем данные из полей
    const data = {
        fullname: document.getElementById("fullname").value,
        email: document.getElementById("email").value,
        password: document.getElementById("password").value
    };

    // Отправляем данные в save.py
    fetch("save.py", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Ошибка отправки");
        }

        // ✅ ЕСЛИ ДАННЫЕ ОТПРАВИЛИСЬ — ПЕРЕХОД
        window.location.href = "BetPage.html";
    })
    .catch(error => {
        alert("Не удалось отправить данные");
        console.log(error);
    });
});