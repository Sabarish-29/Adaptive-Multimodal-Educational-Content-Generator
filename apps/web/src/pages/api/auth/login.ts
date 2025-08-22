import type { NextApiRequest, NextApiResponse } from 'next';
import jwt from 'jsonwebtoken';

const SECRET = process.env.AUTH_SECRET || 'dev-secret';

export default function handler(req: NextApiRequest, res: NextApiResponse){
  if(req.method !== 'POST') return res.status(405).json({ error: 'method' });
  const { username, password } = req.body || {};
  if(!username || !password) return res.status(400).json({ error: 'missing' });
  // DEV: accept any, role inference
  const role = username.includes('inst') ? 'instructor' : 'learner';
  const token = jwt.sign({ sub: username, role }, SECRET, { expiresIn: '2h' });
  res.setHeader('Set-Cookie', `auth_jwt=${token}; HttpOnly; Path=/; SameSite=Lax${process.env.NODE_ENV==='production'?'; Secure':''}`);
  res.json({ ok:true, role });
}
