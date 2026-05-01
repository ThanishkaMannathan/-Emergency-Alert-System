/* Film grain background effect */
(function () {
  const canvas = document.getElementById("grain");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let w, h;

  function resize() {
    w = canvas.width  = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  function draw() {
    const img = ctx.createImageData(w, h);
    const d   = img.data;
    for (let i = 0; i < d.length; i += 4) {
      const v = (Math.random() * 255) | 0;
      d[i] = d[i+1] = d[i+2] = v;
      d[i+3] = 18;
    }
    ctx.putImageData(img, 0, 0);
    requestAnimationFrame(draw);
  }
  draw();
})();
