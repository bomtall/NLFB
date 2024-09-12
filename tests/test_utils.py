import NLFB.utils as utils
import pytest

# command to run: pytest tests

@pytest.mark.parametrize(
        'args,kwargs,expected', 
        [
            ([[[1,2,3], [1,2,3,4,5], [1]], 5], dict(), [[1,2,3,None,None], [1,2,3,4,5], [1,None,None,None,None]]),
            ([[['a','','c',''], [1,2,3,4,5], [1]], 5], dict(), [['a',None,'c',None,None], [1,2,3,4,5], [1,None,None,None,None]])
        
        ]
)
def test_pad_data(args, kwargs, expected):
    assert utils.pad_data(*args, **kwargs) == expected
    

