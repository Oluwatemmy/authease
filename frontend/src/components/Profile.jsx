import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axiosInstance from '../utils/axiosInstance'
import { toast } from 'react-toastify'

const Profile = () => {
    const navigate=useNavigate()
    const user = JSON.parse(localStorage.getItem('user'))
    const jwt_access = JSON.parse(localStorage.getItem('access'))

    useEffect(() => {
        if (jwt_access === null && !user) {
            navigate("/login")
        }else{
            getSomeData()
        }
    }, [jwt_access, user])

    const refresh=JSON.parse(localStorage.getItem('refresh'))

    const getSomeData = async () => {
        try {
            const resp = await axiosInstance.get("/test_auth/");
            // if (resp.status === 200) {
            //     console.log(resp.data);
            // }
            console.log(resp.data)
        } catch (error) {
            console.error("Error fetching data", error);
            toast.error("Error")
        }
    }

    const handleLogout = async () => {
        try {
            const res = await axiosInstance.post("/logout/", { "refresh_token": refresh });
            if (res.status === 200) {
                localStorage.removeItem('access');
                localStorage.removeItem('refresh');
                localStorage.removeItem('user');
                navigate("/login");
                toast.success("Logout Successful");
            }
        } catch (error) {
            console.error("Logout failed", error);
            toast.error("Logout failed");
        }
    }

    return (
        <div className='container'>
            <h2>Hi {user && user.names}</h2>
            <p style={{textAlign:"center"}}>Welcome to your Profile</p>
            <button onClick={handleLogout} className='logout-btn'>Logout</button>
        </div>
    )
}

export default Profile;