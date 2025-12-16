const form = document.getElementById("loginForm");
const errorText = document.getElementById("errorText");

form.addEventListener("submit", function (event) {
    event.preventDefault(); // отменяем стандартную отправку

    // очищаем прошлую ошибку
    errorText.textContent = "";

    const data = {
        email: document.getElementById("email").value,
        password: document.getElementById("password").value
    };

    fetch("login.py", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {

        /*
          Ожидаем от Python:
          { "success": true } или { "success": false }
        */

        if (result.success === true) {
            // ✅ УСПЕХ — ПЕРЕХОД
            window.location.href = "BetPage.html";
        } else {
            // ❌ ОШИБКА — ПОКАЗЫВАЕМ ТЕКСТ
            errorText.textContent = "Неверная почта или пароль. Попробуйте ещё раз.";
        }

    })
    .catch(error => {
        errorText.textContent = "Ошибка сервера. Попробуйте позже.";
        console.log(error);
    });
});