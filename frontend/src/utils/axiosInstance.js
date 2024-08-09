import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import dayjs from 'dayjs';


// if token == localStorage.getItem('access'):
//      return JSON.parse(localStorage.getItem('access'))
// else:
//      return null
// explanaton for line 10, 11, 18

const token=localStorage.getItem('access') ? JSON.parse(localStorage.getItem('access')) : ""
const refresh_token=localStorage.getItem('refresh') ? JSON.parse(localStorage.getItem('refresh')) : ""

const baseURL="http://localhost:8000/api/v1/auth"

const axiosInstance=axios.create({
    baseURL:baseURL,
    'Content-Type':'application/json',
})

// Alter defaults after axiosInstance has been created
axiosInstance.defaults.headers.common['Authorization'] = token ? `Bearer ${token}` : "";

axiosInstance.interceptors.request.use( async req =>{
    if (token) {
        req.headers.Authorization = token ? `Bearer ${token}` : ""
        const user = jwtDecode(token)
        const isExpired=dayjs.unix(user.exp).diff(dayjs()) < 1
        if (!isExpired) {
            return req
        } else {
            const res = await axios.post(`${baseURL}/token/refresh/`, {refresh:refresh_token})
            console.log(res.data)
            if (res.status === 200) {   
                const newToken = res.data.access;
                localStorage.setItem('access', JSON.stringify(newToken))
                req.headers.Authorizaton=newToken ? `Bearer ${newToken}` : "";
                return req
            }else{
                const res = await axios.post(`${baseURL}/logout/`, {'refresh_token': refresh_token})
                if (res.status === 200) {
                    localStorage.removeItem('access')
                    localStorage.removeItem('refresh')
                    localStorage.removeItem('user')
                }
            }
        }
    }
    return req
})

console.log("axiosInstance: ")

export default axiosInstance;