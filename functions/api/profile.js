import { json, requireUser, validUsername, cleanText } from '../_lib/auth.js';
export async function onRequestGet({env,request}) {
 const user=await requireUser(request,env);
 if(!user)return json({error:'Unauthorized'},401);
 const profile=await env.DB.prepare('SELECT id,username,display_name,bio,github_url,created_at FROM users WHERE auth_subject=?').bind(user.sub).first();
 return json({profile:profile||null});
}
export async function onRequestPost({env,request}) {
 const auth=await requireUser(request,env);
 if(!auth)return json({error:'Unauthorized'},401);
 let input;try{input=await request.json()}catch{return json({error:'Invalid JSON'},400)}
 const username=String(input.username||'').toLowerCase().trim();
 const name=cleanText(input.display_name,80),bio=cleanText(input.bio||'',500);
 if(!validUsername(username)||!name)return json({error:'Invalid username or display name'},400);
 const gh=input.github_url?String(input.github_url):null;
 if(gh&&(!/^https:\/\/github\.com\/[a-z\d-]+\/?$/i.test(gh)))return json({error:'Invalid GitHub URL'},400);
 const current=await env.DB.prepare('SELECT id,username FROM users WHERE auth_subject=?').bind(auth.sub).first();
 if(current&&current.username!==username)return json({error:'Username is permanent; contact support for changes'},409);
 try{
 if(current)await env.DB.prepare('UPDATE users SET display_name=?,bio=?,github_url=?,updated_at=CURRENT_TIMESTAMP WHERE id=?').bind(name,bio,gh,current.id).run();
 else await env.DB.prepare('INSERT INTO users(auth_subject,username,display_name,bio,github_url) VALUES(?,?,?,?,?)').bind(auth.sub,username,name,bio,gh).run();
 }catch{return json({error:'Username unavailable or database error'},409)}
 const profile=await env.DB.prepare('SELECT id,username,display_name,bio,github_url,created_at FROM users WHERE auth_subject=?').bind(auth.sub).first();
 return json({profile});
}
