let dataGeneralPath = "/static/regions_fire/";
let monthNames = [
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек"
];

let graphColors = {
    'Природный пожар': {
        borderColor: 'rgb(0, 102, 204)',
        backgroundColor: 'rgba(0, 102, 204, 0.2)'
    },
    'Лесной пожар': {
        borderColor: 'rgb(34, 139, 34)',
        backgroundColor: 'rgba(34, 139, 34, 0.2)'
    },
    'Контролируемый пал': {
        borderColor: 'rgb(255, 165, 0)',
        backgroundColor: 'rgba(255, 165, 0, 0.2)'
    },
    'Неконтролируемый пал': {
        borderColor: 'rgb(220, 20, 60)',
        backgroundColor: 'rgba(220, 20, 60, 0.2)'
    },
    'Торфяной пожар': {
        borderColor: 'rgb(139, 69, 19)',
        backgroundColor: 'rgba(139, 69, 19, 0.2)'
    }
};

let currentRegionId = 1
let charts = []

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
    currentRegionId = regionId;
    document.getElementById('modal-title').textContent = `${regionFullName}`;
    document.getElementById('modal').classList.add('active');
    
    let filename = regionId + '.json';
    fetch(dataGeneralPath + filename)
    .then(response => response.json())
    .then(data =>   {        
        createGraph('nature-fires', data.fires['Природный пожар'], 'Природный пожар');
        createGraph('forest-fires', data.fires['Лесной пожар'], 'Лесной пожар');
        createGraph('control-fires', data.fires['Контролируемый пал'], 'Контролируемый пал');
        createGraph('uncontrol-fires', data.fires['Неконтролируемый пал'], 'Неконтролируемый пал');
        createGraph('troph-fires', data.fires['Торфяной пожар'], 'Торфяной пожар');
    });
}

function closeModal() {
    destroyAllCharts();
    document.getElementById('modal').classList.remove('active');
}

function destroyAllCharts() {
    for (let key in charts) {
        charts[key].destroy();
        charts[key] = null;
    }
}

document.getElementById('ml-analysis-btn').addEventListener('click', function() {
    if(currentRegionId) {
        window.location.href = `/ml-analysis/?region_id=${currentRegionId}`;
    }
});


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
    let canvas = document.getElementById(fire_type_id);
    let ctx = canvas.getContext('2d');

    let groupedData = groupByYearAndMonth(fire_dates);
    let labels = Object.keys(groupedData);
    let data = Object.values(groupedData);

    labels.push('окт 2021');
    data.push(0);

    graphColors[label]

    charts[fire_type_id] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: graphColors[label].borderColor,  // Цвет линии
                backgroundColor: graphColors[label].backgroundColor,  // Цвет заливки
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
window.createGraph = createGraph;
window.groupByYearAndMonth = groupByYearAndMonth;
window.monthNames = monthNames;
window.graphColors = graphColors;