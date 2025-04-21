async function fetchData() {
    const data = await fetch("/api/radar").then(res => res.json());
    const axis = await fetch("/api/radar_axis").then(res => res.json());
    console.log("DATA:", data);
    console.log("AXIS META:", axis);
    drawRadarChart(data, axis);
  }
  
  function drawRadarChart(data, axisMeta) {
    const features = Object.keys(axisMeta);
    const width = 600, height = 600;
    const margin = 60;
  
    const svg = d3.select("#radar").append("svg")
      .attr("width", width + margin * 2)
      .attr("height", height + margin * 2)
      .append("g")
      .attr("transform", `translate(${(width / 2) + margin}, ${(height / 2) + margin})`);
  
    const radialScale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, 250]);
  
    const ticks = [0.2, 0.4, 0.6, 0.8, 1.0];
  
    svg.selectAll("circle")
      .data(ticks)
      .join("circle")
      .attr("fill", "none")
      .attr("stroke", "lightgray")
      .attr("r", d => radialScale(d));
  
    svg.selectAll(".ticklabel")
      .data(ticks)
      .join("text")
      .attr("class", "ticklabel")
      .attr("x", 5)
      .attr("y", d => -radialScale(d))
      .text(d => d);
  
    function angleToCoordinate(angle, value) {
      let x = Math.cos(angle) * radialScale(value);
      let y = Math.sin(angle) * radialScale(value);
      return { x, y };
    }
  
    let featureData = features.map((f, i) => {
      let angle = (Math.PI / 2) + (2 * Math.PI * i / features.length);
      return {
        name: f,
        angle: angle,
        line_coord: angleToCoordinate(angle, 1),
        label_coord: angleToCoordinate(angle, 1.2)
      };
    });
  
    svg.selectAll("line")
      .data(featureData)
      .join("line")
      .attr("x1", 0)
      .attr("y1", 0)
      .attr("x2", d => d.line_coord.x)
      .attr("y2", d => d.line_coord.y)
      .attr("stroke", "black");
  
    svg.selectAll(".axislabel")
      .data(featureData)
      .join("text")
      .attr("x", d => d.label_coord.x)
      .attr("y", d => d.label_coord.y)
      .text(d => d.name.replace(/_/g, " "))
      .attr("font-size", "13px")
      .attr("font-weight", "bold")
      .attr("text-anchor", "middle");
  
    const line = d3.line()
      .x(d => d.x)
      .y(d => d.y);
  
    const colors = d3.schemeCategory10;
  
    function normalize(val, min, max) {
      return (max - min) === 0 ? 0.5 : (val - min) / (max - min);
    }
  
    function getPathCoordinates(data_point) {
      const coords = features.map((f, i) => {
        const angle = (Math.PI / 2) + (2 * Math.PI * i / features.length);
        const val = normalize(+data_point[f], +axisMeta[f].min, +axisMeta[f].max);
        return angleToCoordinate(angle, val);
      });
      coords.push(coords[0]); 
      return coords;
    }
  
    const paths = data.map(d => getPathCoordinates(d));
    svg.selectAll(".data-path")
      .data(paths)
      .join("path")
      .attr("class", "data-path")
      .attr("d", line.curve(d3.curveLinearClosed))
      .attr("stroke-width", 3)
      .attr("stroke", (_, i) => colors[i % colors.length])
      .attr("fill", (_, i) => colors[i % colors.length])
      .attr("fill-opacity", 0.3)
      .attr("stroke-opacity", 1);
  
    const legend = d3.select("#radar").append("div")
    .attr("class", "legend")
    .style("margin-top", "20px");
  
    svg.selectAll(".data-path")
    .data(paths)
    .join("path")
    .attr("class", (d, i) => `data-path polygon-${i}`)
    .attr("d", line.curve(d3.curveLinearClosed))
    .attr("stroke-width", 3)
    .attr("stroke", (_, i) => colors[i % colors.length])
    .attr("fill", (_, i) => colors[i % colors.length])
    .attr("fill-opacity", 0.3)
    .attr("stroke-opacity", 1);
  
    data.forEach((d, i) => {
    const id = `poly-toggle-${i}`;
    const entry = legend.append("div").style("margin-bottom", "6px");
  
    entry.append("input")
      .attr("type", "checkbox")
      .attr("id", id)
      .attr("checked", true)
      .on("change", function () {
        const visible = this.checked;
        d3.select(`.polygon-${i}`)
          .style("display", visible ? "block" : "none");
      });
  
    entry.append("label")
      .attr("for", id)
      .style("margin-left", "6px")
      .html(`<span style="display:inline-block; width:15px; height:15px; background:${colors[i % colors.length]}; margin-right:6px;"></span>${d._id || d.obesity_class}`);
    });
  
  }
  
  fetchData();
  