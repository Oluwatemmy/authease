import React, { useState } from 'react'
import { toast } from 'react-toastify'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const Login = () => {

    const navigate = useNavigate()

    const [logindata, setLoginData]=useState({
        email:"",
        password:""
    })

    const [error, setError]=useState("")
    const [isloading, setIsLoading]=useState(false)

    const handleOnChange = (e) => {
        setLoginData({...logindata, [e.target.name]: e.target.value})
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        const {email, password}=logindata
        if (!email || !password) {
            setError("Email and Password are required")
        } else{
            setIsLoading(true)
            const res = await axios.post("http://localhost:8000/api/v1/auth/login/", logindata)
            const response = res.data
            console.log(response)
            setIsLoading(false)
            const user={
                "email": response.email,
                "names": response.full_name
            }
            if (res.status === 200) {
                localStorage.setItem("user", JSON.stringify(user))
                localStorage.setItem("access", JSON.stringify(response.access_token))
                localStorage.setItem("refresh", JSON.stringify(response.refresh_token))
                navigate("/dashboard")
                toast.success("Login Successful")
            }
        }
    }

    return (
        <div>
            <div className='form-container'>
                <div className='wrapper' style={{width:"100%"}}>
                    <h2>Login</h2>
                    <form onSubmit={handleSubmit}>
                        {isloading && (
                            <p>Loading...</p>
                        )}
                        <div className="form-group">
                            <label htmlFor="">Email address:</label>
                            <input type="text" 
                            className="email-form"
                            name="email"
                            value={logindata.email}
                            onChange={handleOnChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">Password:</label>
                            <input type="password" 
                            className="email-form"
                            name="password"
                            value={logindata.password}
                            onChange={handleOnChange}
                            />
                        </div>
                        <input type="submit" value="Submit" className='submitButton'></input>
                    </form>
                </div>
            </div>
        </div>
    )
}

export default Login