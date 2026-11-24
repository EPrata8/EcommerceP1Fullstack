const dados = JSON.parse(document.getElementById('dados').textContent);
const css = getComputedStyle(document.documentElement);
const cor = n => css.getPropertyValue(n).trim();
const brl = v => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

Chart.defaults.color = cor('--suave');
Chart.defaults.borderColor = cor('--linha');
Chart.defaults.font.family = cor('--sans');

const porStatus = { Pago: cor('--salvia'), Pendente: cor('--ambar'), Cancelado: cor('--vinho') };
const rosca = document.getElementById('grafStatus');
if (rosca) {
  new Chart(rosca, {
    type: 'doughnut',
    data: {
      labels: dados.status.map(x => x.status),
      datasets: [{
        data: dados.status.map(x => x.total),
        backgroundColor: dados.status.map(x => porStatus[x.status]),
        borderColor: cor('--painel'),
        borderWidth: 3,
      }],
    },
    options: { maintainAspectRatio: false, cutout: '66%', plugins: { legend: { position: 'bottom' } } },
  });
}

const serie = document.getElementById('grafMes');
if (serie) {
  new Chart(serie, {
    type: 'bar',
    data: {
      labels: dados.mes.map(x => x.mes),
      datasets: [
        {
          type: 'bar',
          label: 'Receita',
          data: dados.mes.map(x => x.receita),
          backgroundColor: cor('--latao') + 'cc',
          borderRadius: 6,
          yAxisID: 'y',
        },
        {
          type: 'line',
          label: 'Pedidos',
          data: dados.mes.map(x => x.total),
          borderColor: cor('--salvia'),
          backgroundColor: cor('--salvia'),
          tension: 0.35,
          pointRadius: 4,
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'bottom' },
        tooltip: { callbacks: { label: c => c.dataset.yAxisID === 'y' ? ` Receita: ${brl(c.parsed.y)}` : ` Pedidos: ${c.parsed.y}` } },
      },
      scales: {
        y: { beginAtZero: true, ticks: { callback: v => brl(v) } },
        y1: { beginAtZero: true, position: 'right', grid: { drawOnChartArea: false }, ticks: { precision: 0 } },
      },
    },
  });
}
