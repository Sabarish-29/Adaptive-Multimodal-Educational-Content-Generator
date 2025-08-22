import React, { useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Stack } from '../components/Stack';

function Inner(){
  const { user, login, logout } = useAuth();
  const [username, setUsername] = useState('learner1');
  const [password, setPassword] = useState('');
  if(user){
    return (
      <div style={{ maxWidth:420, margin:'72px auto' }}>
        <Card title="Session">
          <p style={{ margin:'0 0 12px' }}>Logged in as <strong>{user.name}</strong> ({user.role})</p>
          <Button onClick={logout}>Logout</Button>
        </Card>
      </div>
    );
  }
  return (
    <div style={{ maxWidth:420, margin:'72px auto' }}>
      <Card title="Login">
        <Stack gap={12}>
          <label style={{ display:'flex', flexDirection:'column', gap:4 }}>
            <span style={{ fontSize:12 }}>Username</span>
            <input type="text" name="username" aria-label="Username" value={username} onChange={e=>setUsername(e.target.value)} style={{ padding:8, border:'1px solid #2A303B', borderRadius:6, background:'#161A21', color:'inherit' }} />
          </label>
          <label style={{ display:'flex', flexDirection:'column', gap:4 }}>
            <span style={{ fontSize:12 }}>Password</span>
            <input type="password" name="password" aria-label="Password" value={password} onChange={e=>setPassword(e.target.value)} style={{ padding:8, border:'1px solid #2A303B', borderRadius:6, background:'#161A21', color:'inherit' }} />
          </label>
          <Button onClick={()=>login(username, password)}>Login</Button>
        </Stack>
      </Card>
    </div>
  );
}

export default function LoginPage(){
  return <Inner />;
}
