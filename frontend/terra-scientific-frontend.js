const TERRA_API = "http://127.0.0.1:8000";

const TERRA_CAPABILITIES = {
  variableGroups: {
    Atmosphere: ["Temperature","Tmax","Tmin","MSLP","Geopotential height","Wind U/V","Relative humidity","Specific humidity","Precipitation","Radiation"],
    AirQuality: ["PM2.5","PM10","O3","NO2","SO2","CO","Aerosols","Custom atmospheric constituent"],
    Ocean: ["Sea-surface temperature","Salinity","Currents","Sea level","Chlorophyll-a"],
    LandBiosphere: ["NDVI","LAI","Soil moisture","Evapotranspiration","Land-surface temperature","Biomass"],
    Cryosphere: ["Snow","Sea ice","Ice variables"],
    Extremes: ["Heatwave","Cold wave","Drought","Extreme rainfall","Dust event","Fire-weather event"]
  },
  analyses: ["Raw field","Mean","Maximum","Minimum","Climatology","Anomaly","Trend","Percentile","Extreme event","PCA","SOM","Correlation","Regression","Model comparison","Bias","MAE","RMSE","Forecast","Scenario"],
  figures: ["Scientific map","Seasonal multi-panel map","Time series","Heatmap","Vector map","SOM maps","Model comparison"],
  exports: ["PNG","SVG","PDF","CSV","NetCDF"]
};

function populateSelect(select, values){
  if(!select) return;
  select.innerHTML = "";
  values.forEach(v=>{
    const o=document.createElement("option");
    o.value=v; o.textContent=v; select.appendChild(o);
  });
}

function initialiseTERRAScientificUI(){
  const analysis=document.querySelector("#terra-analysis");
  const variable=document.querySelector("#terra-variable");
  const group=document.querySelector("#terra-variable-group");
  if(group){
    populateSelect(group,Object.keys(TERRA_CAPABILITIES.variableGroups));
    group.addEventListener("change",()=>{
      populateSelect(variable,TERRA_CAPABILITIES.variableGroups[group.value]);
    });
    group.dispatchEvent(new Event("change"));
  }
  populateSelect(analysis,TERRA_CAPABILITIES.analyses);
}

async function runTERRAAnalysis({file,variable,analysis,unit="",bbox=""}){
  const fd=new FormData();
  fd.append("file",file);
  fd.append("variable",variable||"");
  fd.append("analysis",analysis||"mean");
  fd.append("unit",unit);
  fd.append("bbox",bbox);
  const response=await fetch(`${TERRA_API}/analyse`,{method:"POST",body:fd});
  if(!response.ok) throw new Error(await response.text());
  return await response.json();
}

async function loadTERRACapabilities(){
  const response=await fetch(`${TERRA_API}/capabilities`);
  return response.json();
}

window.TERRA_CAPABILITIES=TERRA_CAPABILITIES;
window.initialiseTERRAScientificUI=initialiseTERRAScientificUI;
window.runTERRAAnalysis=runTERRAAnalysis;
window.loadTERRACapabilities=loadTERRACapabilities;
