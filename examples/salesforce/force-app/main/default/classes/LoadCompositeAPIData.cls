// This code can be run in Anonymous Apex to load data from Github Gists
// sfdx force:apex:execute -f src/classes/LoadCompositeAPIData.cls -f ./examples/salesforce/LoadCompositeAPIData.apex -u Snowfakery__qa
// or
// cci task run execute_anon --path examples/salesforce/LoadCompositeAPIData.apex --org qa
//
// Or called from other Apex, like the LoadSnowfakeryJSONData which exposes a
// an Invocable endpoint

public class LoadCompositeAPIData { 

    // Load one of three JSON formats. 
    //
    // 1. One with a top-level key called "tables" which links to other
    //    composite graph payload jsons, like this:
    //
    //  https://gist.githubusercontent.com/prescod/6f3aebafde63971d1093549c3bef4e41/raw/8885df2618ece474c196d5d94b594dd2b5961c71/csvw_metadata.json
    //
    //  Create the files with snowfakery.experimental.SalesforceCompositeAPIOutput.Folder
    //
    // 2. One with a top-level key called "data" which embeds compsite graph
    //    payloads as strings. Like this:
    //
    //  https://gist.githubusercontent.com/prescod/6220fa27d8493be954be949c9f57f2b2/raw/b603a4d11ef20f0a30e79260322baa52f969068d/out.bundle.json'
    //
    //  Create the files with snowfakery.experimental.SalesforceCompositeAPIOutput.Bundle
    //
    // 3. One which is just a single composite graph payload like this:
    //
    //  https://gist.githubusercontent.com/prescod/13302ecbd08fc3fe92db7d6ee4614d25/raw/c88949d2170c7c11f94958ec672ec8b972cc10d4/composite.json
    //
    //  Which is recognizable by its top-level "graphs" key.
    //
    //  Create the files with snowfakery.experimental.SalesforceCompositeAPIOutput

    public static void loadJsonSet(String set_url){
        String json_record_sets = downloadJSON(set_url);
        Map<String, Object> data = (Map<String, Object>)Json.deserializeUntyped(json_record_sets);
        List<Object> tables = (List<Object>)data.get('tables');
        if(tables != null){
            loadDistributedJsonSet(tables);
            return;
        }

        List<Object> graph_jsons = (List<Object>)data.get('data');
        if(graph_jsons != null){
            loadBundledJsonSet(graph_jsons);
            return;
        }

        List<Object> graphs = (List<Object>)data.get('graphs');
        if(graphs != null){
            loadRecords(json_record_sets);
            return;
        }

    }

    // optimized method for a single composite graph (<500 records)
    // This method doesn't parse the JSON to see what's in it.
    public static void loadSingleJsonGraphPayload(String url) {
        System.debug('Loading JSON ' + url);
        String json_records = downloadJSON(url);
        loadRecords(json_records);
        System.debug('Loaded JSON ' + url);
    }

    public static void loadDistributedJsonSet(List<Object> tables){
        for(Object table_url: tables){
            Map<String, Object> url_obj = (Map<String, Object>) table_url;
            String url = (String)url_obj.get('url');
            loadSingleJsonGraphPayload(url);
        }
    }

    public static void loadBundledJsonSet(List<Object> graph_jsons){
        for(Object graph_json: graph_jsons){
            loadRecords((String)graph_json);
        }
    }

    private static String downloadJSON(String url){
        HttpResponse response = makeHTTPCall('GET', url, null);
        return response.getBody();
    }

    private static HttpResponse makeHTTPCall(String method, String url, String post_body){
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
         System.debug(url);
        return h.send(request);
    }

    private static void loadRecords(String json_records){
        String error = null;
        String graph_url = System.URL.getSalesforceBaseUrl().toExternalForm() + '/services/data/v54.0/composite/graph';
        HttpResponse response = makeHTTPCall('POST', graph_url, json_records);
        String response_body = response.getBody();
        if(response.getStatusCode()!=200){
            error = 'Error creating objects! ' + response.getStatus() + ' ' + response_body;
        }else{
            error = parseResponse(response_body);
        }

        if(error!=null){
            System.debug('Error: ' + error);
            // System.debug('DOWNLOADED Data');
            // System.debug(response_body);
            CalloutException e = new CalloutException( error);
            throw e;
        }
    }

    private static String parseResponse(String response) {
        Map<String, Object> graph_parse = (Map<String, Object>)Json.deserializeUntyped(response);
        return parseError(graph_parse);
    }

    private static String parseError(Map<String, Object> graph_parse){
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