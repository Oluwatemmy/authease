import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import axiosInstance from '../utils/axiosInstance'

const Signup = () => {
    const navigate = useNavigate()
    const [searchparams] = useSearchParams()

    const [formdata, setFormData]=useState({
        email:'',
        first_name:'',
        last_name:'',
        password:'',
        confirm_password:''
    })

    const handleSignInWthGoogle = async (response)=>{
        const payload = response.credential
        const server_res = await axios.post("http://localhost:8000/api/v1/oauth/google/", {"access_token": payload})
        console.log(server_res)
        const user={
            "email": server_res.data.email,
            "names": server_res.data.full_name
        }
        if (server_res.status === 200) {
            localStorage.setItem("user", JSON.stringify(user))
            localStorage.setItem("access", JSON.stringify(server_res.data.access_token))
            localStorage.setItem("refresh", JSON.stringify(server_res.data.refresh_token))
            navigate("/dashboard")
            toast.success("Login Successfull")
        }
    }

    useEffect(() =>{
        /* global google */
        google.accounts.id.initialize({
            client_id: import.meta.env.VITE_CLIENT_ID,
            callback: handleSignInWthGoogle
        });
        google.accounts.id.renderButton(
            document.getElementById('signInDiv'),
            { theme: 'outline', size: 'large', text:"continue_with", shape:"circle", width:"280" }
            );
    }, [])

    const [error, setError]=useState("")

    const handleOnChange = (e) => {
        setFormData({...formdata, [e.target.name]: e.target.value})
    }

    const {email, first_name, last_name, password, confirm_password}=formdata

    const handleSubmit = async (e) => {
        e.preventDefault()
        if(!email || !first_name || !last_name || !password || !confirm_password) {
            setError("Please fill all the fields")
        }else{
            console.log(formdata)
            // make call to api
            const res = await axios.post('http://localhost:8000/api/v1/auth/register/', formdata)
            // check our responses
            const response = res.data
            console.log(response)
            if (res.status === 201) {
                // redirect to verifyemail component
                navigate("/otp/verify")
                toast.success(response.message)
            }
            // server error pass to error
        }
    }
    console.log(error)

const handleSignInWthGithub = () => {
    window.location.assign(`https://github.com/login/oauth/authorize/?client_id=${import.meta.env.VITE_GITHUB_ID}`)
}

const send_code_to_backend = async () => {
    if (searchparams) {
        try {
            const code = searchparams.get('code')
            const response = await axios.post("http://localhost:8000/api/v1/oauth/github/", {"code": code})
            const result = response.data
            console.log(result)
            if (response.status === 200) {
                const user = {
                    "email": result.email,
                    "names": result.full_name
                }
            localStorage.setItem("user", JSON.stringify(user))
            localStorage.setItem("access", JSON.stringify(result.access_token))
            localStorage.setItem("refresh", JSON.stringify(result.refresh_token))
            navigate("/dashboard")
            toast.success("Login Successfull")
            }
        } catch (error) {
            console.log(error)
        }
    }
}

let code = searchparams.get('code')
useEffect(() => {
    if (code) {
        send_code_to_backend()
    }
}, [code])

    return (
        <div>
            <div className='form-container'>
                <div className='wrapper' style={{width:"100%"}}>
                    <h2>Create Account</h2>
                    <form onSubmit={handleSubmit}>
                        <p style={{color:'red', padding:"1px"}}>{error ? error : ""}</p>
                        <div className="form-group">
                            <label htmlFor="">Email address:</label>
                            <input type="text" 
                            className="email-form"
                            name="email"
                            value={email}
                            onChange={handleOnChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">First Name:</label>
                            <input type="text" 
                            className="email-form"
                            name="first_name"
                            value={first_name}
                            onChange={handleOnChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">Last Name:</label>
                            <input type="text" 
                            className="email-form"
                            name="last_name"
                            value={last_name}
                            onChange={handleOnChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">Password:</label>
                            <input type="password" 
                            className="email-form"
                            name="password"
                            value={password}
                            onChange={handleOnChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">Confirm Password:</label>
                            <input type="password" 
                            className="email-form"
                            name="confirm_password"
                            value={confirm_password}
                            onChange={handleOnChange}
                            />
                        </div>
                        <input type="submit" value="Submit" className='submitButton'></input>
                    </form>
                    <h3 className='text-option'>Or </h3>
                    <div className='githubContainer'>
                        <button onClick={handleSignInWthGithub}>Sign up with Github</button>
                    </div>
                    <div className='googleContainer' id='signInDiv'>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Signup