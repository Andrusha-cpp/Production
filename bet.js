// Список кандидатов
const candidates = [
    {
        name: "Анна Иванова",
        description: "Студентка 2 курса, активистка",
        photo: "img/anna.jpg"
    },
    {
        name: "Мария Петрова",
        description: "Участница олимпиад, волонтёр",
        photo: "img/maria.jpg"
    },
    {
        name: "Екатерина Смирнова",
        description: "Спортсменка, лидер команды",
        photo: "img/ekaterina.jpg"
    }
];

let currentIndex = 0;

// DOM-элементы
const nameEl = document.getElementById("candidateName");
const descEl = document.getElementById("candidateDesc");
const photoEl = document.getElementById("candidatePhoto");

// Функция отображения кандидата
function showCandidate(index) {
    const candidate = candidates[index];
    nameEl.textContent = candidate.name;
    descEl.textContent = candidate.description;
    photoEl.src = candidate.photo;
}

// Кнопки
document.getElementById("prevBtn").addEventListener("click", () => {
    currentIndex--;
    if (currentIndex < 0) {
        currentIndex = candidates.length - 1;
    }
    showCandidate(currentIndex);
});

document.getElementById("nextBtn").addEventListener("click", () => {
    currentIndex++;
    if (currentIndex >= candidates.length) {
        currentIndex = 0;
    }
    showCandidate(currentIndex);
});

// Показываем первого кандидата при загрузке
showCandidate(currentIndex);