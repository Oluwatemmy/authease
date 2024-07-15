import React, { useState } from 'react'

const Signup = () => {

    const [formdata, setFormData]=useState({
        email:'',
        first_name:'',
        last_name:'',
        password:'',
        confirm_password:''
    })

    const [error, setError]=useState("")

    const handleOnChange = (e) => {
        setFormData({...formdata, [e.target.name]: e.target.value})
    }

    const {email, first_name, last_name, password, confirm_password}=formdata

    const handleSubmit = (e) => {
        e.preventDefault()
        if(!email || !first_name || !last_name || !password || !confirm_password) {
            setError("Please fill all the fields")
        }else{
            console.log(formdata)
        }
    }
    console.log(error)

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
                        <button>Sign up with Github</button>
                    </div>
                    <div className='googleContainer'>
                        <button>Sign up with Google</button>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Signup