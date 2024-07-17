import axios from 'axios'


// if token == localStorage.getItem('access'):
//      return JSON.parse(localStorage.getItem('access'))
// else:
//      return null
// explanaton for line 10, 11, 18

const token=localStorage.getItem('access') ? JSON.parse(localStorage.getItem('access')) : ""
const refresh_token=localStorage.getItem('refresh') ? JSON.parse(localStorage.getItem('refresh')) : ""

const baseUrl='http://localhost:8000/api/v1/auth/'

const axiosInstance=axios.create({
    baseUrl:baseUrl,
    'Content-type':'applcation/json',
    headers:{ Authorization: localStorage.getItem('access') ? `Bearer ${token}` : null }
})