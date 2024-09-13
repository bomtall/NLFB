from NLFB.src import utils
import pytest
import numpy as np

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
    


@pytest.mark.parametrize(
        'args,kwargs,expected', 
        [
            ([0], dict(), "no correlation"),
            ([], dict(value=0), "no correlation"),
            ([], dict(value=10), ""),
            ([1], dict(), "perfect positive correlation"),
            ([0.8], dict(), "strong positive correlation"),
            ([0.6], dict(), "moderate positive correlation"),
            ([0.3765], dict(), "weak positive correlation"),
            #([None], dict(), ""),
        ]
)
def test_explain_pearsons_r(args, kwargs, expected):
    assert utils.describe_pearsons_r(*args, **kwargs) == expected

@pytest.mark.parametrize(
        'args,kwargs,expected', 
        [
            ([None], dict(), ""),

        ]
)
def test_pearsons_error(args, kwargs, expected):  
    """  
    Test that a FileNotFoundError is raised when the file does not exist  
    """  
    with pytest.raises(TypeError) as e:  
        utils.describe_pearsons_r(*args, **kwargs)  
    assert str(e.value) == 'Incorrect type'
