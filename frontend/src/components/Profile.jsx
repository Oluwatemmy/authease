import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const Profile = () => {
    const navigate=useNavigate()
    const user = JSON.parse(localStorage.getItem('user'))
    const jwt_access = JSON.parse(localStorage.getItem('access'))

    useEffect(() => {
        if (jwt_access === null && !user) {
            navigate("/login")
        }
    }, [])

    return (
        <div className='container'>
            <h2>Hi {user && user.names}</h2>
            <p style={{textAlign:"center"}}>Welcome to your Profile</p>
            <button className='logout-btn'>Logout</button>
        </div>
    )
}

export default Profile