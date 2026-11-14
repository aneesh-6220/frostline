// NorthLink: pull MODIS 8-day snow cover (MOD10A2/MYD10A2) and land-surface temperature (MOD11A2)
// at the 9 corridor points from Microsoft Planetary Computer (public, no login).
// HOW TO RUN: open https://planetarycomputer.microsoft.com/api/stac/v1/collections/modis-11A2-061 in any browser
// (it must be on that origin), open DevTools console, paste this file. The shell/WebFetch cannot reach the site; a browser can.
// Poll: window.__job.done / window.__job.total (432 jobs, about 15-20 min). When window.__job.finished is true,
// export window.__job.rows as CSV. Columns: location_id, collection, sensor(MOD|MYD), tile, start_date, end_date, value1, value2
//   10A2: value1 = Maximum_Snow_Extent (25 no snow, 37 lake, 50 cloud, 100 lake ice, 200 snow), value2 = Eight_Day_Snow_Cover (bit flags/percent)
//   11A2: value1 = LST_Day_1km, value2 = LST_Night_1km (raw; Kelvin = raw * 0.02; 0 = no data)
// After finishing, re-run any entries listed in window.__job.errors (transient "Failed to fetch" happens).
// Keep MOD and MYD separate; never mix them in one series. Single 500 m / 1 km pixel at an approximate point: indicative only.
const L={dettah_bay:[62.43,-114.34],aklavik_delta:[68.29,-134.37],deline:[65.19,-123.43],liard_fort_simpson:[61.86,-121.35],norman_wells_fgh:[65.77,-127.73],nahanni_butte:[61.03,-123.38],tibbitt_contwoyto:[64.5,-110.5],sambaa_ke:[60.44,-121.24],wrigley_tulita:[64.07,-124.5]};
const C={'modis-10A2-061':['Maximum_Snow_Extent','Eight_Day_Snow_Cover'],'modis-11A2-061':['LST_Day_1km','LST_Night_1km']};
const R=6371007.181,T=1111950.5197;
function tile(lat,lon){const x=R*lon*Math.PI/180*Math.cos(lat*Math.PI/180),y=R*lat*Math.PI/180;const h=Math.floor((x+20015109.354)/T),v=Math.floor((10007554.677-y)/T);return 'h'+String(h).padStart(2,'0')+'v'+String(v).padStart(2,'0')}
window.__job={rows:[],done:0,total:0,errors:[],finished:false,tiles:{}};
const jobs=[];
for(const [loc,[lat,lon]] of Object.entries(L)){window.__job.tiles[loc]=tile(lat,lon);for(const [col,assets] of Object.entries(C))for(let y=2001;y<=2024;y++)jobs.push({loc,lat,lon,col,assets,y,tile:tile(lat,lon)})}
window.__job.total=jobs.length;
async function sj(j){
 try{
  let s;
  for(let a=0;a<4;a++){const r=await fetch('/api/stac/v1/search',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({collections:[j.col],intersects:{type:'Point',coordinates:[j.lon,j.lat]},datetime:`${j.y}-10-01T00:00:00Z/${j.y+1}-04-15T23:59:59Z`,limit:400})});if(r.ok){s=await r.json();break}await new Promise(r=>setTimeout(r,1500));}
  if(!s)throw new Error('search failed');
  const feats=s.features.filter(f=>f.id.includes('.'+j.tile+'.'));
  for(const f of feats){
   let ok=false,txt='';
   for(let a=0;a<4&&!ok;a++){
    const url=`/api/data/v1/item/point/${j.lon},${j.lat}?collection=${j.col}&item=${f.id}`+j.assets.map(x=>'&assets='+x).join('');
    const r=await fetch(url);txt=await r.text();
    if(r.ok){const d=JSON.parse(txt);window.__job.rows.push([j.loc,j.col,f.id.slice(0,3),j.tile,f.properties.start_datetime.slice(0,10),f.properties.end_datetime?f.properties.end_datetime.slice(0,10):'',...d.values]);ok=true}
    else await new Promise(r=>setTimeout(r,1500));
   }
   if(!ok)window.__job.errors.push(j.loc+' '+f.id+' '+txt.slice(0,80));
  }
  if(!feats.length)window.__job.errors.push('no feats '+j.loc+' '+j.col+' '+j.y);
 }catch(e){window.__job.errors.push(j.loc+' '+j.col+' '+j.y+' '+e)}
 window.__job.done++;
}
(async()=>{let i=0;const w=Array.from({length:12},async()=>{while(i<jobs.length){await sj(jobs[i++])}});await Promise.all(w);window.__job.finished=true})();
