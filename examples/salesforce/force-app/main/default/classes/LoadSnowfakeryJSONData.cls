public class LoadSnowfakeryJSONData {
    @InvocableMethod(label='Load Snowfakery Data Bundle'
        description='Load a Snowfakery data bundle file into an Org by URL (JSON Graph API format)')
    public static void loadJsonSet(List<String> json_urls){
        for(String json_url: json_urls){
            LoadCompositeAPIData.loadJsonSet(json_url);
        }
    }
}