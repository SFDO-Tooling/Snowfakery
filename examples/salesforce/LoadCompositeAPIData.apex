// This code can be run in Anonymous Apex to load data from Github Gists
// sfdx force:apex:execute -f ./examples/salesforce/LoadCompositeAPIData.apex -u Snowfakery__qa
// or
// cci task run execute_anon --path examples/salesforce/LoadCompositeAPIData.apex --org qa


public class LoadCompositeAPIData { 
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
            CalloutException e = new CalloutException( error);
            throw e;
        }
    }

    private String parseResponse(String response) {
        Map<String, Object> graph_parse = (Map<String, Object>)Json.deserializeUntyped(response);
        return parseError(graph_parse);
    }

    private String parseError(Map<String, Object> graph_parse){
        String rc = null;
        List<Object> graphs = (List<Object>)graph_parse.get('graphs');
        for(Object graph: graphs){
            Map<String, Object> graphobj = (Map<String, Object>) graph;
            boolean success = (boolean)graphobj.get('isSuccessful');
            if(success) continue;
            Map<String, Object> graphResponse = (Map<String, Object>)graphobj.get('graphResponse');
            List<Object> compositeResponse = (List<Object>)graphResponse.get('compositeResponse');
            for(Object single_response: compositeResponse){
                Map<String, Object> single_response_obj = (Map<String, Object>)single_response;
                Integer status = (Integer)single_response_obj.get('httpStatusCode');
                if(status!=200 && status!=201){
                    List<Object> body = (List<Object>)single_response_obj.get('body');
                    Map<String, Object> body_obj = (Map<String, Object>)body[0];
                    if(rc==null && (String)body_obj.get('errorCode')!='PROCESSING_HALTED') {
                        System.debug('Error: ' + body.toString());
                        rc = body_obj.toString();
                        break;
                    }
                }
            }
        }

        return rc;
    }
}

JSONSObjectLoader loader = new JSONSObjectLoader();
LoadCompositeAPIData loader = new LoadCompositeAPIData();
// experimentally, much more than 20 hits a cumulative
// maximum time allotted for callout error
for (Integer i = 0; i < 20;) {
    loader.LoadJson('https://gist.githubusercontent.com/prescod/13302ecbd08fc3fe92db7d6ee4614d25/raw/c88949d2170c7c11f94958ec672ec8b972cc10d4/composite.json');
    System.debug(++i);
    loader.LoadJson('https://gist.githubusercontent.com/prescod/86a64c63fe294b8123b895b489852e6f/raw/e8ae51b7f5af5db6b5b800a3f9c40ebd0c7a1998/composite2.json');
    System.debug(++i);
    loader.LoadJson('https://gist.githubusercontent.com/prescod/21b4a0b9fe5cac171abb8f6a633cb39a/raw/cd7e0f1025a61946b4f923999afa546f099282fa/composite3.json');
    System.debug(++i);
}
