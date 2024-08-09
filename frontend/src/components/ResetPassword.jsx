import React, { useState } from "react"
import { useNavigate, useParams } from "react-router-dom";
import axiosInstance from "../utils/axiosInstance";
import { toast } from "react-toastify";

const ResetPassword = () => {
    const navigate = useNavigate()
    const { uid, token } = useParams()
    const [newpasswords, setNewPasswords] = useState({
        password: "",
        confirm_password: ""
    })

    const handleOnChange = (e) => {
        setNewPasswords({ ...newpasswords, [e.target.name]: e.target.value })
    }

    const data = {
        password: newpasswords.password,
        confirm_password: newpasswords.confirm_password,
        'uidb64': uid,
        'token': token
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        // make api call
        const response = await axiosInstance.patch("/set_new_password/", data)
        const result = response.data
        if (response.status === 200) {
            navigate("/login")
            toast.success(result.message)
        }
    }



    return (
        <div>
            <div className='form-container'>
                <div className='wrapper' style={{ width: "100%" }}>
                    <h2>Enter your New Password</h2>
                    <form action="" onSubmit={handleSubmit}>
                        <div className='form-group'>
                            <label htmlFor="">New Password:</label>
                            <input type="password"
                                className='email-form'
                                name="password"
                                value={newpasswords.password}
                                onChange={handleOnChange}
                            />
                        </div>
                        <div className='form-group'>
                            <label htmlFor="">Confirm Password</label>
                            <input type="password"
                                className='email-form'
                                name="confirm_password"
                                value={newpasswords.confirm_password}
                                onChange={handleOnChange}
                            />
                        </div>
                        <button type='submit' className='vbtn'>Submit</button>
                    </form>
                </div>
            </div>
        </div>
    )
}

export default ResetPassword;