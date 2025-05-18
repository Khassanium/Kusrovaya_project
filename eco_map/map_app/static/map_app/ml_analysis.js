
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const regionId = params.get('region_id');
  if (!regionId) return;

  fetch(`/static/regions_fire/${regionId}.json`)
    .then(r => r.json())
    .then(data => {
      createGraph('nature-fires', data.fires['Природный пожар'], 'Природный пожар');
      createGraph('forest-fires', data.fires['Лесной пожар'], 'Лесной пожар');
      createGraph('control-fires', data.fires['Контролируемый пал'], 'Контролируемый пал');
      createGraph('uncontrol-fires', data.fires['Неконтролируемый пал'], 'Неконтролируемый пал');
      createGraph('troph-fires', data.fires['Торфяной пожар'], 'Торфяной пожар');
    });
});