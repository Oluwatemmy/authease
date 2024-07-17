import { useState } from 'react'
import { ToastContainer } from 'react-toastify';
import "react-toastify/dist/ReactToastify.css";
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Signup, Login, Profile, VerifyEmail, ForgetPassword } from "./components";
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <BrowserRouter>
        <ToastContainer />
          <Routes>
            <Route path="/" element={<Signup/>} />
            <Route path="/login" element={<Login/>} />
            <Route path="/dashboard" element={<Profile/>} />
            <Route path="/otp/verify" element={<VerifyEmail/>} />
            <Route path="/forget_password" element={<ForgetPassword/>} />
          </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
