const drawWinPercentageGraph = (canvasId, percentage, isMatches) => {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const r = Math.min(centerY, centerX) * 0.8;
  const endAngle = -2 * Math.PI * (percentage / 100) - (Math.PI / 2);

  ctx.beginPath();
  ctx.arc(centerX, centerY, r, -Math.PI / 2, endAngle, true);
  ctx.lineWidth = 25;

  const grd = ctx.createConicGradient(0, centerX, centerY, true);
  grd.addColorStop(0, isMatches ? "#cdeac0" : "#dfe7fd");
  grd.addColorStop(1, isMatches ? "#8cb369" : "#a0c4ff");
  ctx.strokeStyle = grd;
  ctx.stroke();
}

const drawTotalGraph = (canvasId, playerData) => {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  canvas.width = canvas.clientWidth;
  canvas.height = canvas.clientHeight;

  const matchData = {
    label: "Match",
    data: playerData.elo_history,
    borderColor: "#8cb369",
    fill: false,
    lineTension: 0.3,
  };
  const pointsData = {
    label: "Points",
    data: playerData.points_elo_history,
    borderColor: "#a0c4ff",
    fill: false,
    lineTension: 0.3,
  };

  const lineGraph = new Chart(canvas, {
    type: "line",
    data: {
      labels: playerData.elo_history,
      datasets: [matchData, pointsData],
    },
    options: {
      maintainAspectRatio: true,
      events: [],
      animation: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          display: false,
        },
      },
      elements: {
        point: {
          radius: 0,
        },
      },
    }
  });

}


const drawGraphs = () => {
  console.log(PLAYER_DATA);
  drawWinPercentageGraph("matchesWinPercentageCanvas", PLAYER_DATA.win_perc, true);
  drawWinPercentageGraph("pointsWinPercentageCanvas", PLAYER_DATA.round_win_perc, false);
  drawTotalGraph("eloGraphCanvas", PLAYER_DATA);
}
