分析当前项目，@api_solver.py是主文件，帮我完成以下修改：

1. @results.json 是程序保存的结果缓存文件，在代码逻辑中添加自动删除超时的task，例如过1小时（增加可配置项）
2. 规范返回参数，例如相同的请求，有时候返回CAPTCHA_NOT_READY文本，有时候返回json内容，不便于调用
3. 利用GitHub action添加多平台docker支持（arm64，amd64等），在不影响代码的前提下简化代码逻辑，仅支持headless=True，browser_type=camoufox的情况，仅保留thread，proxy，host，port，和[第一点要求中的最大缓存时长]等参数，移除不必要的参数和相关情况判断
