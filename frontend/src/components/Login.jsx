import { React } from 'react'

const Login = () => {
    return (
        <div>
            <div className='form-container'>
                <div className='wrapper' style={{width:"100%"}}>
                    <h2>Login</h2>
                    <form>
                        <div className="form-group">
                            <label htmlFor="">Email address:</label>
                            <input type="text" 
                            className="email-form"
                            name="email"
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="">Password:</label>
                            <input type="password" 
                            className="email-form"
                            name="password"
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