import React, { useState } from 'react'

const Signup = () => {
    return (
        <div>
            <div className='form-container'>
                <div className='wrapper' style={{width:"100%"}}>
                    <h2>Create Account</h2>
                    <form>
                        <div className="form-group">
                            <label htmlFor="">Email address:</label>
                            <input type="text" 
                            className="email-form"
                            name="email"
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">First Name:</label>
                            <input type="text" 
                            className="email-form"
                            name="first_name"
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">Last Name:</label>
                            <input type="text" 
                            className="email-form"
                            name="last_name"
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">Password:</label>
                            <input type="password" 
                            className="email-form"
                            name="password"
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">Confirm Password:</label>
                            <input type="password" 
                            className="email-form"
                            name="confirm_password"
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