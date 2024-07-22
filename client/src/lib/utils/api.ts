
// Base URL for all API calls

// export const BACKEND_LOCAL_HOST = 'http://192.168.2.62:5000';      // this should be the flask address, it might change to be aware
// export const BACKEND_LOCAL_HOST = 'http://192.168.110.120:5000';      // like this 
// TODO: originally, set that manually, but later when you use docker or Kubernetes, we can solve that elgantly
export const BACKEND_LOCAL_HOST = 'http://localhost:5000';      // like this 
export const BASE_URL = BACKEND_LOCAL_HOST;            // local network


// secure (https) network 
export const SECURE_HOST = 'https://';


// Specific API endpoints
export const API_ENDPOINTS = {

    REGISTER: `${BASE_URL}/auth/api/register`,
    MATCH: `${BASE_URL}/auth/api/match`,


    UPLOAD_DATA: `${BASE_URL}/upload/api/upload_data`,
    UPLOAD_SAMPLE: `${BASE_URL}/upload/api/upload_sample`,
    WORKFLOW_COMMIT: `${BASE_URL}/upload/api/workflow_commit`,
    FETCH_LOCKED_WORKFLOW: `${BASE_URL}/upload/api/fetch_locked_workflow`,
    FETCH_ALL_WORKFLOW: `${BASE_URL}/upload/api/fetch_all_workflow`,
    UPLOAD_FILE: `${BASE_URL}/upload/api/upload_file`,
    DOWNLOAD_FILE: `${BASE_URL}/upload/api/download_file`,


    FETCH_COLLECTIONS: `${BASE_URL}/search/api/collections`,
    FETCH_KEYS: `${BASE_URL}/search/api/keys`,
    FETCH_SAMPLE_TOKEN: `${BASE_URL}/search/api/get_sample_tokens`,
    FETCH_WORKFLOW_TOKEN: `${BASE_URL}/search/api/get_workflow_tokens`,
    SEARCH_RESULTS: `${BASE_URL}/search/api/searched_result`,


    EXCHANGE_RATE: `${BASE_URL}/extra/api/exchange_rate`,

};



// Helper function to construct URLs with query parameters
export function constructUrl(endpoint: string, params: Record<string, string>): string {

    // this URL type will automatically append url required parameters in, like "?"
    const url = new URL(endpoint);
    Object.entries(params).forEach(([key, value]) => {
        // Use encodeURIComponent for both key and value
        url.searchParams.append(key, value);
    });
    // console.log("URL as string:", url.toString());
    return url.toString();
}




// ------------- explain ---------------
// when you encode the url, it's encoded internally 
// but you console log them, they will be displayed properly for readibility 
// so don't worry, and if you want to see how it looks, you uncomment the below function 
// and you can see on the browser console, should look like this:
// Output: http://localhost:5000/search/api/searched_result?collection=my%20collection&key=some%20key&value=search%20value%20with%20spaces%20%26%20special%20chars


// Example usage
// const url = constructUrl(API_ENDPOINTS.SEARCH_RESULTS, {
//     collection: "my collection",
//     key: "some key",
//     value: "search value with spaces & special chars"
// });
// console.log("Final URL:", url);

