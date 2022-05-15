// This code can be run in Anonymous Apex to load data from Github Gists
// sfdx force:apex:execute -f paulignore/composite/callout.apex -u SFDX_USERALIAS

public class JSONSObjectLoader { 
    public void loadJson(String url) {
        String json_records = downloadJSON(url);
        loadRecords(json_records);
        System.debug('Loaded JSON ' + url);
    }

    public String downloadJSON(String url){
        HttpResponse response = makeHTTPCall('GET', url, null);
        return response.getBody();
    }

    public HttpResponse makeHTTPCall(String method, String url, String post_body){
        Http h = new Http();
        HttpRequest request = new HttpRequest();
        request.setEndpoint(url);
        request.setMethod(method);
        if(post_body != null){
            request.setHeader('Content-Type', 'application/json');
            request.setBody(post_body);
        }

        request.setHeader('Authorization', 'OAuth ' + UserInfo.getSessionId());
        request.setTimeout(120000);
        return h.send(request);
    }

    public void loadRecords(String json_records){
        String error = null;
        String graph_url = System.URL.getSalesforceBaseUrl().toExternalForm() + '/services/data/v54.0/composite/graph';
        HttpResponse response = makeHTTPCall('POST', graph_url, json_records);
        String response_body = response.getBody();
        parseResponse(response_body);

        if(response.getStatusCode()!=200){
            error = 'Error creating objects! ' + response.getStatus() + ' ' + response_body;
        }else{
            try{
                error = parseResponse(response_body);
            }catch(Exception e){
                error = 'Error creating objects! ' + e.getMessage();
            }
        }

        if(error!=null){
            System.debug('Error: ' + error);
            System.debug('DOWNLOADED Data');
            System.debug(response_body);
            CalloutException e = new CalloutException('Error creating objects! ' + error);
            throw e;
        }
    }

    private String parseResponse(String response) {
        String rc = null;
        Map<String, Object> graph_parse = (Map<String, Object>)Json.deserializeUntyped(response);
        bool success = (bool)graph_parse.get('isSuccessful');
        if (success){
            return null;
        }else{
            return parseError(response);
        }
    }

    private String parseError(Map<String, Object> graph_parse){
        List<Object> graphs = (List<Object>)graph_parse.get('graphs');
        for(Object graph: graphs){
            Map<String, Object> graphobj = (Map<String, Object>) graph;
            Map<String, Object> graphResponse = (Map<String, Object>)graphobj.get('graphResponse');
            List<Object> compositeResponse = (List<Object>)graphResponse.get('compositeResponse');
            for(Object single_response: compositeResponse){
                Map<String, Object> single_response_obj = (Map<String, Object>)single_response;
                Integer status = (Integer)single_response_obj.get('httpStatusCode');
                if(status!=200 && status!=201){
                    List<Object> body = (List<Object>)single_response_obj.get('body');
                    Map<String, Object> body_obj = (Map<String, Object>)body[0];
                    if(rc==null){
                        rc = body_obj.toString();
                        break;
                    }
                    if((String)body_obj.get('errorCode')!='PROCESSING_HALTED'){
                        System.debug('Error: ' + body.toString());
                    }
                }
            }
        }

        return rc;
    }
}

JSONSObjectLoader loader = new JSONSObjectLoader();
for (Integer i = 0; i < 16;) {
    loader.LoadJson('https://gist.githubusercontent.com/prescod/13302ecbd08fc3fe92db7d6ee4614d25/raw/c88949d2170c7c11f94958ec672ec8b972cc10d4/composite.json');
    System.debug(++i);
    loader.LoadJson('https://gist.githubusercontent.com/prescod/86a64c63fe294b8123b895b489852e6f/raw/e8ae51b7f5af5db6b5b800a3f9c40ebd0c7a1998/composite2.json');
    System.debug(++i);
    loader.LoadJson('https://gist.githubusercontent.com/prescod/21b4a0b9fe5cac171abb8f6a633cb39a/raw/cd7e0f1025a61946b4f923999afa546f099282fa/composite3.json');
    System.debug(++i);
}
