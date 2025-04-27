let dataGeneralPath = "/static/regions_fire/";
let monthNames = [
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек"
];
document.addEventListener("DOMContentLoaded", function() {
    const svgObject = document.getElementById('svg-map');

    svgObject.addEventListener('load', function() {
        const svgDoc = svgObject.contentDocument;
        const regions = svgDoc.querySelectorAll('path[id]');

        regions.forEach(region => {
            region.addEventListener('click', function() {
                let regionId = this.getAttribute('id')
                let regionFullName =  this.getAttribute('title');
                showModal(regionFullName, regionId);
            });
        });

    });
});


function showModal(regionFullName, regionId) {
    
    document.getElementById('modal-title').textContent = `${regionFullName}`;
    document.getElementById('modal').classList.add('active');
    
    let filename = regionId + '.json';
    fetch(dataGeneralPath + filename)
    .then(response => response.json())
    .then(data =>   {
        createGraph('nature-fires', data.fires['Природный пожар'], 'Природный пожар');
    });
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

function groupByYearAndMonth(fire_dates) {
    let data = {};
    

    let start = new Date('2012-03-01');
    let end = new Date('2021-09-01');
    while (start <= end) {
        let month = monthNames[start.getMonth()];
        let year = start.getFullYear();
        let label = `${month} ${year}`;
        data[label] = 0;
        start.setMonth(start.getMonth() + 1);
    }

    fire_dates.forEach(date => {
        let d = new Date(date);
        let month = monthNames[d.getMonth()];
        let year = d.getFullYear();
        let label = `${month} ${year}`;
        if (label in data) {
            data[label] += 1;
        }
    });

    return data;
}

function createGraph(fire_type_id, fire_dates, label) {
    document.querySelector('.chart-container').innerHTML = `<canvas id="${fire_type_id}"></canvas>`;
    let ctx = document.getElementById(fire_type_id).getContext('2d');
    let groupedData = groupByYearAndMonth(fire_dates);
    let labels = Object.keys(groupedData);
    let data = Object.values(groupedData);
    labels.push('окт 2021');
    data.push(0);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: 'rgb(10, 36, 36)',  // Цвет линии
                backgroundColor: 'rgba(204, 42, 42, 0.2)',  // Цвет заливки
                fill: true
            }]
        },
        options: {
            maintainAspectRatio: false,  // Отключаем сохранение пропорций
            responsive: true,
            scales: {
                x: {
                    ticks: {
                        autoSkip: false,  // Отключаем автоматическое пропускание
                        maxRotation: 50,  // Поворот меток
                        minRotation: 0,
                        font: {
                            size: 10
                        },
                        padding: 0 // Увеличиваем расстояние между метками оси X

                    },
                    // Оставляем немного пространства справа
                    suggestedMax: labels.length + 1  // Увеличиваем максимальный индекс оси X
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 50
                    }
                }
            }
        }
    });
}