## **How to execute long-running searches (Async search) ?** 

For Long-running searches (search that process huge amount of data or data from frozen tier), you can save a long-running search. 

In this scenario, Kibana processes your request in the background, and you can continue your work. 

After you execute ANY query in Kibana (whether it is in _Discover_ tab or _Dashboard_ ), Kibana sends a request to Elasticsearch which timeout within 2 minutes. 

If your search request timeout, then you rather save your session and review the data later (once it is all loaded in the background): 

1.  Click on the clock icon on top left: 


![](logging_docs/markdown_converted/images/3627156949_af73477548b7497d98af47d4d2d26dab-310326-2149-7528.pdf-0001-06.png)


2. **Save session** . You can name your session for easier finding : 


![](logging_docs/markdown_converted/images/3627156949_af73477548b7497d98af47d4d2d26dab-310326-2149-7528.pdf-0001-08.png)


3.  To review your sessions: 

## a.  Open Stack Management 


![](logging_docs/markdown_converted/images/3627156949_af73477548b7497d98af47d4d2d26dab-310326-2149-7528.pdf-0002-01.png)


## b.  Find your session in _Search Sessions_ 


![](logging_docs/markdown_converted/images/3627156949_af73477548b7497d98af47d4d2d26dab-310326-2149-7528.pdf-0002-03.png)


c.  Review the _**Status**_ column 


![](logging_docs/markdown_converted/images/3627156949_af73477548b7497d98af47d4d2d26dab-310326-2149-7528.pdf-0002-05.png)


