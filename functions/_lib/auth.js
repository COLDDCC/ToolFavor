export function json(data,status=200){return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff'}})}
export function cleanText(x,max){return typeof x==='string'?x.trim().slice(0,max):''}
export function validUsername(x){return /^[a-z][a-z0-9_-]{2,29}$/.test(x)&&!['admin','api','login','register','developers','creators','support','toolfavor'].includes(x)}
function b64urlToBytes(s){const b=atob(s.replace(/-/g,'+').replace(/_/g,'/'));return Uint8Array.from(b,c=>c.charCodeAt(0))}
export async function requireUser(request,env){
 const header=request.headers.get('authorization')||'';
 if(!header.startsWith('Bearer ')||!env.AUTH_JWKS_URL||!env.AUTH_ISSUER||!env.AUTH_AUDIENCE)return null;
 const token=header.slice(7),parts=token.split('.');
 if(parts.length!==3)return null;
 try{
 const headerObj=JSON.parse(new TextDecoder().decode(b64urlToBytes(parts[0])));
 const payload=JSON.parse(new TextDecoder().decode(b64urlToBytes(parts[1])));
 if(headerObj.alg!=='RS256'||!headerObj.kid||payload.iss!==env.AUTH_ISSUER||!(Array.isArray(payload.aud)?payload.aud.includes(env.AUTH_AUDIENCE):payload.aud===env.AUTH_AUDIENCE)||!payload.sub||!Number.isFinite(payload.exp)||payload.exp<=Date.now()/1000)return null;
 const res=await fetch(env.AUTH_JWKS_URL);
 if(!res.ok)return null;
 const jwks=await res.json(),key=jwks.keys.find(k=>k.kid===headerObj.kid&&k.kty==='RSA'&&k.use!=='enc');
 if(!key)return null;
 const cryptoKey=await crypto.subtle.importKey('jwk',key,{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['verify']);
 const ok=await crypto.subtle.verify('RSASSA-PKCS1-v1_5',cryptoKey,b64urlToBytes(parts[2]),new TextEncoder().encode(parts[0]+'.'+parts[1]));
 return ok?{sub:payload.sub}:null;
 }catch{return null}
}
