Method	Endpoint                            Authentication	Success
POST	/api/v1/auth/login	                None	        200
GET	    /api/v1/auth/me	                    Bearer token	200
POST	/api/v1/auth/logout	                Bearer token	200
GET	    /api/v1/students/me	                STUDENT	        200
GET	    /api/v1/clearance/me	            STUDENT	        200
POST    //api/v1/admin/sync/registrar       ADMIN           200